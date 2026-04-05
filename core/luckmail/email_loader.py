# 替换 core/luckmail/email_loader.py 的完整代码如下

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json
import csv
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailStatus(Enum):
    """邮箱状态"""
    ACTIVE = 0
    DISABLED = 1
    EXPIRED = 2


@dataclass
class PurchasedEmail:
    """已购邮箱"""
    address: str
    token: str
    status: int = EmailStatus.ACTIVE.value
    tags: List[str] = field(default_factory=list)
    purchase_id: Optional[int] = None
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None
    use_count: int = 0
    project: Optional[str] = None
    domain: Optional[str] = None
    remark: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []

    def mark_used(self):
        self.use_count += 1
        self.last_used_at = datetime.now().isoformat()

    def add_tag(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


class PurchasedEmailLoader:
    """已购邮箱管理器"""

    def __init__(self, config_dir: Optional[str] = None, file_format: str = 'json'):
        self.config_dir = Path(config_dir or './config/luckmail')
        self.format = file_format
        self.file_path = self.config_dir / f"purchased_emails.{file_format}"
        self.backup_dir = self.config_dir / 'backups'
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self._cache: Dict[str, PurchasedEmail] = {}

    def load(self) -> List[PurchasedEmail]:
        """加载邮箱"""
        if not self.file_path.exists():
            return []

        try:
            if self.format == 'json':
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        email = PurchasedEmail(**item)
                        self._cache[email.address] = email
            elif self.format == 'csv':
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = PurchasedEmail(
                            address=row['address'],
                            token=row['token'],
                            status=int(row.get('status', 0)),
                            tags=row.get('tags', '').split(',') if row.get('tags') else [],
                        )
                        self._cache[email.address] = email
            return list(self._cache.values())
        except Exception as e:
            logger.error(f"Error loading emails: {e}")
            return []

    def save(self) -> bool:
        """保存邮箱"""
        try:
            emails = list(self._cache.values())
            if self.format == 'json':
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump([{
                        'address': e.address,
                        'token': e.token,
                        'status': e.status,
                        'tags': e.tags,
                        'purchase_id': e.purchase_id,
                        'created_at': e.created_at,
                        'last_used_at': e.last_used_at,
                        'use_count': e.use_count,
                        'project': e.project,
                        'domain': e.domain,
                        'remark': e.remark,
                    } for e in emails], f, ensure_ascii=False, indent=2)
            elif self.format == 'csv':
                with open(self.file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['address', 'token', 'status', 'tags', 'use_count'])
                    writer.writeheader()
                    for e in emails:
                        writer.writerow({
                            'address': e.address,
                            'token': e.token,
                            'status': e.status,
                            'tags': ','.join(e.tags),
                            'use_count': e.use_count,
                        })
            return True
        except Exception as e:
            logger.error(f"Error saving emails: {e}")
            return False

    def add_email(self, address: str, token: str, **kwargs) -> PurchasedEmail:
        """添加邮箱"""
        email = PurchasedEmail(address=address, token=token, **kwargs)
        self._cache[address] = email
        return email

    def remove_email(self, address: str) -> bool:
        """移除邮箱"""
        if address in self._cache:
            del self._cache[address]
            return True
        return False

    def get_email(self, address: str) -> Optional[PurchasedEmail]:
        """获取邮箱"""
        return self._cache.get(address)

    def mark_used(self, address: str) -> bool:
        """标记使用"""
        email = self.get_email(address)
        if email:
            email.mark_used()
            return True
        return False

    def disable_email(self, address: str) -> bool:
        """禁用邮箱"""
        email = self.get_email(address)
        if email:
            email.status = EmailStatus.DISABLED.value
            return True
        return False

    def enable_email(self, address: str) -> bool:
        """启用邮箱"""
        email = self.get_email(address)
        if email:
            email.status = EmailStatus.ACTIVE.value
            return True
        return False

    def add_tag(self, address: str, tag: str) -> bool:
        """添加标签"""
        email = self.get_email(address)
        if email:
            email.add_tag(tag)
            return True
        return False

    def remove_tag(self, address: str, tag: str) -> bool:
        """移除标签"""
        email = self.get_email(address)
        if email:
            email.remove_tag(tag)
            return True
        return False

    def get_available(self, exclude_tags: List[str] = None) -> List[PurchasedEmail]:
        """获取可用邮箱"""
        exclude_tags = exclude_tags or []
        return [e for e in self._cache.values()
                if e.status == EmailStatus.ACTIVE.value
                and not any(tag in e.tags for tag in exclude_tags)]

    def get_disabled(self) -> List[PurchasedEmail]:
        """获取禁用邮箱"""
        return [e for e in self._cache.values() if e.status == EmailStatus.DISABLED.value]

    def get_unused(self) -> List[PurchasedEmail]:
        """获取未使用邮箱"""
        return [e for e in self._cache.values() if e.use_count == 0]

    def get_by_tag(self, tag: str) -> List[PurchasedEmail]:
        """按标签获取"""
        return [e for e in self._cache.values() if e.has_tag(tag)]

    def get_stats(self) -> Dict:
        """获取统计"""
        all_emails = list(self._cache.values())
        return {
            'total': len(all_emails),
            'available': len(self.get_available()),
            'disabled': len(self.get_disabled()),
            'unused': len(self.get_unused()),
            'used': len([e for e in all_emails if e.use_count > 0]),
            'total_uses': sum(e.use_count for e in all_emails),
        }

    def count(self) -> int:
        """获取总数"""
        return len(self._cache)

    def backup(self, filename: Optional[str] = None) -> bool:
        """备份"""
        try:
            backup_name = filename or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = self.backup_dir / backup_name
            emails = list(self._cache.values())
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump([{
                    'address': e.address,
                    'token': e.token,
                    'status': e.status,
                    'tags': e.tags,
                    'use_count': e.use_count,
                } for e in emails], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def export_to_csv(self, filepath: str) -> bool:
        """导出CSV"""
        try:
            emails = list(self._cache.values())
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['address', 'token', 'status', 'tags', 'use_count', 'project'])
                writer.writeheader()
                for e in emails:
                    writer.writerow({
                        'address': e.address,
                        'token': e.token,
                        'status': e.status,
                        'tags': ','.join(e.tags),
                        'use_count': e.use_count,
                        'project': e.project or '',
                    })
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def clear(self) -> None:
        """清空"""
        self._cache.clear()

    def get_all(self) -> List[PurchasedEmail]:
        """获取全部"""
        return list(self._cache.values())

import os
import glob

class EmailLoader:
    def __init__(self, directory):
        self.directory = directory

    def load_emails(self):
        email_files = glob.glob(os.path.join(self.directory, '*.txt'))
        emails = []
        for file_path in email_files:
            with open(file_path, 'r') as file:
                emails.extend(file.read().splitlines())
        return emails

# Example usage:
# loader = EmailLoader('/path/to/email/directory')
# emails = loader.load_emails()
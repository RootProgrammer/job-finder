from jira_job_match_insighter.google.google_clients_initializer import GoogleClientsInitializer
from jira_job_match_insighter.log_manager.logger import Logger


class GoogleDocsReader(object):
    google_logger = Logger().setup_logging()
    google_clients_initializer = GoogleClientsInitializer()
    docs_service = google_clients_initializer.docs_service

    @classmethod
    def get_google_doc_content(cls, doc_id):
        if cls.google_clients_initializer.ensure_google_clients_initialized():
            try:
                doc = cls.docs_service.documents().get(documentId=doc_id).execute()
                doc_content = doc.get('body').get('content')
                text = ""
                for value in doc_content:
                    if 'paragraph' in value:
                        elements = value.get('paragraph').get('elements')
                        for elem in elements:
                            text += elem.get('textRun').get('content')

                return text
            except Exception as e:
                cls.google_logger.error(f"Failed to get Google Doc content: {e}")
                return None
        else:
            return None

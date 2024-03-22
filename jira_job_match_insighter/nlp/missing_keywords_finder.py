from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from jira_job_match_insighter.log_manager.logger import Logger


class MissingKeywordsFinder:
    nlp_logger = Logger().setup_logging()

    @classmethod
    def get_missing_keywords(cls, resume_text, job_description_text):
        try:
            stop_words = set(stopwords.words('english'))
            resume_tokens = [w for w in word_tokenize(resume_text.lower()) if w not in stop_words]
            job_desc_tokens = [w for w in word_tokenize(job_description_text.lower()) if w not in stop_words]
            missing_keywords = set(job_desc_tokens) - set(resume_tokens)
            return missing_keywords
        except Exception as e:
            cls.nlp_logger.error(f"Failed to analyze resume with job description: {e}")
            return None

import openai
import requests
import torch
import xml.etree.ElementTree as ET
from decouple import config
from transformers import BertTokenizer, BertModel
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Jira:
    # API_ENDPOINT = input("Enter the Jira API endpoint (e.g.,
    # https://your-domain.atlassian.net/rest/api/latest/issue): ")

    API_ENDPOINT = "https://imranslab.atlassian.net/rest/api/latest/issue"

    # USERNAME = input("Enter your Jira username (associated email address): ")

    USERNAME = "imranul.islam@mail.mcgill.ca"

    # API_TOKEN = input("Enter your Jira API token: ")

    API_TOKEN = config('JIRA_API_TOKEN')

    AUTH = (USERNAME, API_TOKEN)

    @classmethod
    def get_link(cls, issue_number):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.get(cls.API_ENDPOINT + '/' + issue_number, auth=cls.AUTH, headers=headers)

        # Print the response status code
        print("Response Status Code:", response.status_code)

        if response.content:
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                raise ValueError("Received an invalid JSON response from the Jira API.")
        else:
            raise ValueError("Received an empty response from the Jira API.")

        # Print the full response data
        # print("Full Jira API Response:", data)

        # Handle error messages from Jira API
        if 'errorMessages' in data and data['errorMessages']:
            raise ValueError(data['errorMessages'][0])

        # Check if 'fields' is in the response and 'customfield_10054' is in 'fields'
        if 'fields' in data and 'customfield_10054' in data['fields']:
            return data['fields']['customfield_10054']
        else:
            raise KeyError("The expected key ('customfield_10054') was not found in the Jira API response.")


class XMLWriter:
    @staticmethod
    def save_to_xml(feedback, file_name):
        root = ET.Element("Feedback")
        content = ET.SubElement(root, "Content")
        content.text = feedback
        tree = ET.ElementTree(root)
        tree.write(file_name)


class NLPAnalyzer:
    @staticmethod
    def generate_embeddings(text):
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertModel.from_pretrained('bert-base-uncased')
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)

    @staticmethod
    def measure_similarity(embedding1, embedding2):
        return cosine_similarity(embedding1, embedding2)

    @staticmethod
    def extract_keywords(text, n=10):
        vectorizer = CountVectorizer().fit([text])
        return [word for word, count in
                sorted(vectorizer.vocabulary_.items(), key=lambda item: item[1], reverse=True)[:n]]

    @staticmethod
    def compare_keywords(job_keywords, resume_text):
        return [kw for kw in job_keywords if kw not in resume_text]


class OpenAIAnalyzer:
    # openai.api_key = input("Enter your OpenAI API key: ")

    openai.api_key = config('OPENAI_API_KEY')

    @staticmethod
    def compare(missing_keywords, resume_content):
        prompt = (f"Compare the following job description: {missing_keywords} with this resume: {resume_content}. "
                  f"Provide detailed feedback.")
        feedback = None
        try:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
                {"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}])
            feedback = response['choices'][0]['message']['content'].strip()
        except openai.error.RateLimitError as e:
            feedback = f"Rate limit reached: {e}"
        except openai.error.InvalidRequestError as e:
            if 'tokens' in str(e):
                feedback = "This model's maximum token limit exceeded."
            else:
                feedback = f"An error occurred: {e}"
        except Exception as e:
            feedback = f"An unexpected error occurred: {e}"
        return feedback


if __name__ == "__main__":
    # issue_number = input("Enter the Jira issue number: ")
    issue_number = "IOMT-884"

    # resume_link = input("Enter the Google Docs link for the resume: ")
    resume_link = "https://docs.google.com/document/d/1-eDP23td-nkIy-SY3ap1KELAP8EIigMBo6mfrUTfC3k/edit?usp=sharing"

    xml_file_name = input("Enter the name for the XML file to save feedback: ") + ".xml"

    link = Jira.get_link(issue_number)
    job_description = None
    resume_response = requests.get(resume_link)
    resume_content = resume_response.text

    job_embedding = NLPAnalyzer.generate_embeddings(job_description)
    resume_embedding = NLPAnalyzer.generate_embeddings(resume_content)
    similarity = NLPAnalyzer.measure_similarity(job_embedding, resume_embedding)
    print(f"Similarity between job description and resume: {similarity[0][0]:.2f}")
    job_keywords = NLPAnalyzer.extract_keywords(job_description)
    missing_keywords = NLPAnalyzer.compare_keywords(job_keywords, resume_content)
    print("Missing keywords in the resume:", ", ".join(
        missing_keywords) if missing_keywords else "All important keywords from the job description are present in "
                                                   "the resume.")

    feedback = OpenAIAnalyzer.compare(missing_keywords, resume_content)
    XMLWriter.save_to_xml(feedback, xml_file_name)

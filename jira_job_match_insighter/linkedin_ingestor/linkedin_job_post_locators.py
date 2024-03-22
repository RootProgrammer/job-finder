class LinkedinJobPostLocators:
    # These are the main attributes of the objects a LinkedIn job post will consist of
    # It can be edited and expanded more attributes
    def __init__(self):
        self.job_title = "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/a/h2"
        self.job_link = "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/a"
        self.company_name = "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/h4/div[1]/span[1]/a"
        self.location = "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/h4/div[1]/span[2]"
        self.time_ago = "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/h4/div[2]/span"
        self.be_among_first_xx_applicant = (
            "/html/body/div[1]/div/section/"
            "div[2]/section/"
            "div/div[1]/div/h4/div[2]/figure/figcaption"
        )
        self.job_description = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/div/section/div"
        self.similar_jobs = "/html/body/div[1]/div/main/div/h1/span[2]"
        self.job_criteria_list = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/ul"

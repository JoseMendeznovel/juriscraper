"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.

History:
    - 2022-01-31: Updated by William E. Palin
    - 2022-02-18: Status verification, cases name cleaning and extract_from_text, @satsuki-chan
"""

import re
from typing import Any, Dict

from juriscraper.lib.string_utils import clean_string, convert_date_string
from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.state.co.us/Courts/Court_of_Appeals/Case_Announcements/"

    def _process_html(self) -> None:
        """Process the HTML

        This is an odd little site, where they just post unpublished and published opinions without links.
        Fortunately, its easy enough to crawl and the pattern for the URLs is pretty consistent. (i think)

        The URL looks like this https://www.courts.state.co.us/Courts/Court_of_Appeals/Opinion/[YEAR]/[DOCKET]-[PD].pdf

        I think PD means Published Decision, but I'm not sure.  If it is then the URLs should work everytime.
        The caveat is that the Supreme Court seems to have some lag between switching to 2022 from 2021 bucket but
        the URLS are given there.

        :return: None
        """
        rows = self.html.xpath("//p")
        date = rows[0].text_content()
        date_year = convert_date_string(date)

        if "P U B L I S H E D O P I N I O N S" != clean_string(
            rows[1].text_content()
        ):
            return {}
        for row in rows[2:]:
            row_text = clean_string(row.text_content())
            if row_text == "U N P U B L I S H E D O P I N I O N S":
                break
            docket, name = row_text.split(" ", 1)
            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "url": f"https://www.courts.state.co.us/Courts/Court_of_Appeals/Opinion/{date_year.year}/{docket}-PD.pdf",
                    "status": "Published",
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary
        Notes for 'Citation':
            - Reporter key for this court: 'COA'
            - Type for a state: 2
        :param scraped_text: Text of scraped content
        :return: metadata
        """
        match_re = r"The.*SUMMARY.*?(?P<citation>\d{4}COA\d+).*?No\. (?P<docket>\d+CA\d+), (?P<headnotes>.*?)\n{2,}(?P<summary>.*?)COLORADO COURT OF APPEALS"
        match = re.findall(match_re, scraped_text, re.M | re.S)
        metadata = {}
        if match:
            volume, page = match[0][0].split("COA")
            metadata = {
                "OpinionCluster": {
                    "docket_number": match[0][1],
                    "headnotes": clean_string(match[0][2]),
                    "summary": clean_string(match[0][3]),
                },
                "Citation": {
                    "volume": volume,
                    "reporter": "COA",
                    "page": page,
                    "type": 2,
                },
            }
        return metadata

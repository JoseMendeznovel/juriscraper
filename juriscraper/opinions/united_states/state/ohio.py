"""Scraper for the Supreme Court of Ohio
CourtID: ohio
Court Short Name: Ohio
Author: Andrei Chelaru
Reviewer: mlr
History:
 - Stubbed out by Brian Carver
 - 2014-07-30: Finished by Andrei Chelaru
 - 2015-07-31: Redone by mlr to use ghost driver. Alas, their site used to be
               great, but now it's terribly frustrating.
 - 2021-12-26: Remove selenium
"""
from datetime import date

from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_index = 0
        self.year = str(date.today().year)
        self.url = "https://www.supremecourtofohio.gov/rod/docs/"
        self.court_id = self.__module__
        # The required data properties
        self.data = {
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$MainContent$ddlCourt": f"{self.court_index}",
            "ctl00$MainContent$ddlDecidedYearMin": f"{self.year}",
            "ctl00$MainContent$ddlDecidedYearMax": f"{self.year}",
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$btnSubmit": "Submit",
            "ctl00$MainContent$ddlRowsPerPage": "50",
        }

    def _process_html(self):
        if not self.test_mode_enabled():
            # Update event validation and view state to enable posting
            self.data["__EVENTVALIDATION"] = self.html.xpath(
                "//input[@id='__EVENTVALIDATION']"
            )[0].get("value")
            self.data["__VIEWSTATE"] = self.html.xpath(
                "//input[@id='__VIEWSTATE']"
            )[0].get("value")
            self.url = "https://www.supremecourt.ohio.gov/rod/docs/"
            response = self.request["session"].post(self.url, data=self.data)
            self.html = html.fromstring(response.text)

        # Skip the header rows and the footer rows
        for row in self.html.xpath(
            ".//table[@id='MainContent_gvResults']//tr"
        )[3:-2]:
            self.cases.append(
                {
                    "judge": row.xpath(".//td[4]//text()")[0],
                    "docket": row.xpath(".//td[2]//text()")[0],
                    "date": row.xpath(".//td[6]//text()")[0],
                    "name": row.xpath(".//a/text()")[0],
                    "url": row.xpath(".//a")[0].get("href"),
                    "status": "Published",
                    "neutral_citation": row.xpath(".//td[8]//text()")[0],
                    "summary": row.xpath(".//td[3]//text()")[0],
                }
            )

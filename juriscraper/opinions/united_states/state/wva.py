import requests

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.courtswv.gov/supreme-court/opinions.html"
        self.court_id = self.__module__
        self.cell_path = "//table/tbody/tr/td[%d]"

    def _get_case_names(self):
        return [
            anchor.text_content()
            for anchor in self.html.xpath(f"{self.cell_path % 3}/a[1]")
        ]

    def _get_download_urls(self):
        return [
            href
            for href in self.html.xpath(f"{self.cell_path % 3}/a[1]/@href")
        ]

    def _get_case_dates(self):
        return [
            convert_date_string(cell.text_content().strip())
            for cell in self.html.xpath(self.cell_path % 1)
        ]

    def _get_docket_numbers(self):
        return [
            cell.text_content().lower().strip()
            for cell in self.html.xpath(self.cell_path % 2)
        ]

    def _get_precedential_statuses(self):
        codes = {
            "MD": "Published",
            "SO": "Published",
            "PC": "Published",
            "SEP": "Separate",
        }
        return self.decode_cell_text(self.cell_path % 5, codes)

    def _get_nature_of_suit(self):
        # List is sourced from JS in scraped HTML
        codes = {
            "CR-F": "Felony (non-Death Penalty)",
            "CR-M": "Misdemeanor",
            "CR-O": "Criminal-Other",
            "TCR": "Tort, Contract, and Real Property",
            "PR": "Probate",
            "FAM": "Family",
            "JUV": "Juvenile",
            "CIV-O": "Civil-Other",
            "WC": "Workers Compensation",
            "TAX": "Revenue (Tax)",
            "ADM": "Administrative Agency-Other",
            "MISC": "Appeal by Right-Other",
            "OJ-H": "Habeas Corpus",
            "OJ-M": "Writ Application-Other",
            "OJ-P": "Writ Application-Other",
            "L-ADM": "Bar Admis   sion",
            "L-DISC": "Bar Discipline/Eligibility",
            "L-DISC-O": "Bar/Judiciary Proceeding-Other",
            "J-DISC": "Bar/Judiciary Proceeding-Other",
            "CERQ": "Certified Question",
            "OJ-O": "Original Proceeding/Appellate Matter-Other",
            "POST": "Post-Conviction Appeal",
        }
        return self.decode_cell_text(self.cell_path % 4, codes)

    def decode_cell_text(self, path, codes):
        results = []
        for cell in self.html.xpath(path):
            code = cell.text_content().strip()
            results.append(codes[code] if code in codes else "Unknown")
        return results

    def check_url(self, url):
        return (
            requests.head(
                url,
                allow_redirects=False,
                headers={"User-Agent": "Juriscraper"},
            ).status_code
            != 200
        )

    def _post_parse(self):
        """Check newest 50 opinions for broken links.

        No good explanation here. But it seems that sometimes there links just
        dont work. Instead we should just do head requests on the newest 50
        opinions and drop them.
        """

        to_be_removed = [
            index
            for index, url in enumerate(self.download_urls[:50])
            if self.check_url(url)
        ]
        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is not None:
                new_item = self.remove_elements(item, to_be_removed)
                self.__setattr__(attr, new_item)

    @staticmethod
    def remove_elements(list_, indexes_to_be_removed):
        return [
            i for j, i in enumerate(list_) if j not in indexes_to_be_removed
        ]

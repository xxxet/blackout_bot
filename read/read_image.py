import cv2
from easyocr import easyocr
from img2table.document import Image
from img2table.ocr import EasyOCR


class ImageRead:
    def __init__(self):
        pass

    # def read_doctr(self):
    #     ocr = DocTR(detect_language=False,
    #         kw={"pretrained": True})
    #     img = Image(src="../group5.jpg")
    #     extracted_tables = img.extract_tables(ocr=ocr)
    #     extracted_tables_implicit = img.extract_tables(ocr=ocr, implicit_rows=True)
    #
    #     for table in extracted_tables:
    #         self.write("table1.html", table.html_repr(title="Regular table"))
    #     for table in extracted_tables_implicit:
    #         self.write("table1-imp.html", table.html_repr(title="Regular table"))

    # def read_tes(self):
    #     # Define OCR instance, requires prior installation of Tesseract-OCR
    #     ocr = TesseractOCR(lang="ukr")
    #
    #     # Define image
    #     img = Image(src="../group5.jpg")
    #
    #     # Extract tables
    #     extracted_tables = img.extract_tables(ocr=ocr)
    #     extracted_tables_implicit = img.extract_tables(ocr=ocr, implicit_rows=True)
    #
    #     table_implicit_rows = extracted_tables_implicit.pop()
    #     table = extracted_tables.pop()
    #
    #     # display_html(table.html_repr(title="Regular table"), raw=True)
    #     # display_html(table_implicit_rows.html_repr(title="Table with implicit rows"), raw=True)
    #
    #     # self.write("table1.html", table.html_repr(title="Regular table"))
    #     # self.write("table1-imp.html", table_implicit_rows.html_repr(title="Regular table"))
    #
    #     # table_img = cv2.imread("../group5.jpg")
    #     # for table in extracted_tables:
    #     #     for row in table.content.values():
    #     #         for cell in row:
    #     #             cv2.rectangle(table_img, (cell.bbox.x1, cell.bbox.y1), (cell.bbox.x2, cell.bbox.y2), (255, 0, 0), 2)
    #     #
    #     # PILImage.fromarray(table_img)
    #
    #     # img.to_xlsx('../tables.xlsx',
    #     #             ocr=tesseract_ocr,
    #     #             implicit_rows=True,
    #     #             borderless_tables=False,
    #     #             min_confidence=50)

    #
    # for page, tables in extracted_tables.items():
    #     for idx, table in enumerate(tables):
    #         display_html(table.html_repr(title=f"Page {page + 1} - Extracted table n°{idx + 1}"), raw=True)

    def write(self, name, content):
        f = open(name, "w")
        f.write(content)
        f.close()

    def just_eacyocr(self):
        reader = easyocr.Reader(['uk'])
        result = reader.readtext("../group5.jpg")
        for line in result:
            print(line)
        pass

    def read_easyocr(self):
        ocr = EasyOCR(["uk"])
        img = Image(src="../group5.jpg", detect_rotation=True)
        extracted_tables = img.extract_tables(ocr=ocr)
        extracted_tables_implicit = img.extract_tables(ocr=ocr, implicit_rows=True)

        for table in extracted_tables:
            self.write("table1.html", table.html_repr(title="Regular table"))
        for table in extracted_tables_implicit:
            self.write("table1-imp.html", table.html_repr(title="Regular table"))

        table_img = cv2.imread("../group5.jpg")

        for table in extracted_tables:
            for row in table.content.values():
                for cell in row:
                    cv2.rectangle(table_img, (cell.bbox.x1, cell.bbox.y1), (cell.bbox.x2, cell.bbox.y2), (255, 0, 0), 2)
        cv2.imshow('ImageWindow', table_img)
        cv2.waitKey()

    def example(self):
        img = Image(src="../group5.jpg", detect_rotation=True)

        # Extract tables
        extracted_tables = img.extract_tables(implicit_rows=True,
                                              borderless_tables=True,
                                              min_confidence=30)

        table_img = cv2.imread("../group5.jpg")
        for table in extracted_tables:
            for row in table.content.values():
                for cell in row:
                    cv2.rectangle(table_img, (cell.bbox.x1, cell.bbox.y1), (cell.bbox.x2, cell.bbox.y2), (255, 0, 0), 2)
        cv2.imshow('ImageWindow', table_img)
        cv2.waitKey()


if __name__ == '__main__':
    ImageRead().example()

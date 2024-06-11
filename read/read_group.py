import csv
import logging
import os
from math import sqrt

import cv2
import numpy as np
from cv2 import kmeans, TERM_CRITERIA_MAX_ITER, TERM_CRITERIA_EPS, KMEANS_RANDOM_CENTERS
from img2table.document import Image
from numpy import float32, unique


def display_table(img):
    cv2.imshow('ImageWindow', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def visualise_cells(img, cell_l, cell_r):
    cv2.rectangle(img, cell_l, cell_r,
                  (255, 0, 0), 1)


class ReadGroup:

    def __init__(self, image_path: str):
        self.outage_table = []
        self.column_width = None
        self.extracted_tables = None
        self.image_path = image_path
        file_name = os.path.basename(self.image_path)
        self.csv_table = os.path.join(os.path.dirname(self.image_path),
                                      os.path.splitext(file_name)[0] + ".csv")
        self.white_cell = (255, 255, 255)
        self.grey_cell = (238, 240, 239)
        self.black_cell = (210, 212, 214)

    def extract_table(self):
        if os.path.isfile(self.csv_table):
            logging.info(f"{self.csv_table} already exists, skipped parsing")
        else:
            img = Image(src=self.image_path, detect_rotation=True)
            self.extracted_tables = img.extract_tables(implicit_rows=True,
                                                       borderless_tables=True,
                                                       min_confidence=50)
            self.read_rows()
            self.save_to_csv()

    def read_rows(self):
        myimg = cv2.imread(self.image_path)
        myimg = cv2.cvtColor(myimg, cv2.COLOR_BGR2RGB)

        table = self.extracted_tables[0]
        header_row = table.content[0]
        # skip first colum and header with labels (day name, time interval)
        table.content.popitem(last=False)
        for row in table.content.values():
            day = []
            first_cell = row[1]
            cur_y = first_cell.bbox.y1
            for i in range(1, 25):
                header_cell = header_row[i]
                cell_l = (header_cell.bbox.x1, cur_y)
                cell_r = (header_cell.bbox.x2, cur_y + header_cell.bbox.x2 - header_cell.bbox.x1)
                cropped_image = myimg[cell_l[1]:cell_r[1], cell_l[0]:cell_r[0]]

                # display_table(cropped_image)

                img_data = cropped_image.reshape(-1, 3)
                criteria = (TERM_CRITERIA_MAX_ITER + TERM_CRITERIA_EPS, 10, 1.0)
                compactness, labels, centers = kmeans(data=img_data.astype(float32), K=5, bestLabels=None,
                                                      criteria=criteria,
                                                      attempts=10, flags=KMEANS_RANDOM_CENTERS)
                colours = centers[labels].reshape(-1, 3)
                u_colors = unique(colours, axis=0, return_counts=True)
                max_index = np.where(u_colors[1] == u_colors[1].max())[0][0]
                max_fr_color = u_colors[0][max_index]
                visualise_cells(myimg, cell_l, cell_r)
                self.determine_cell_type(max_fr_color, day)
            self.outage_table.append(day)
        # display_table(myimg)

    def determine_cell_type(self, cell_color, day_array):
        def calc_delta(cell_color1, cell_color2):
            return sqrt(pow(cell_color1[0] - cell_color2[0], 2)
                        + pow(cell_color1[1] - cell_color2[1], 2)
                        + pow(cell_color1[2] - cell_color2[2], 2))

        delta_black = calc_delta(cell_color, self.black_cell)
        delta_grey = calc_delta(cell_color, self.grey_cell)
        delta_white = calc_delta(cell_color, self.white_cell)

        if delta_black < 5:
            day_array.append("black")
        elif delta_grey < 5:
            day_array.append("grey")
        elif delta_white < 5:
            day_array.append("white")
        else:
            day_array.append("und")

    def save_to_csv(self):
        field_names = [hour for hour in range(0, 24)]
        with open(self.csv_table, 'w') as csvfile:
            write = csv.writer(csvfile)
            write.writerow(field_names)
            write.writerows(self.outage_table)


if __name__ == '__main__':
    rg = ReadGroup("../group4.png")
    rg.extract_table()
    pass

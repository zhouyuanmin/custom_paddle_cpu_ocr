# -*- coding: utf-8 -*-

"""
@author: Mr_zhang
@software: PyCharm
@file: paddle_ocr.py
@time: 2022/10/11 09:22
"""

import re
import os
import cv2
import base64
import numpy as np
import paddleocr


class PaddleOCR:
    """
    PaddleOCR行程卡识别
    """

    BASE_DIR = os.path.dirname(__file__)

    def __init__(self):
        self.ocr = paddleocr.PaddleOCR(use_angle_cls=True, use_gpu=False)

    @staticmethod
    def base64_to_image(base64_code):
        img_data = base64.b64decode(base64_code)
        img_array = np.frombuffer(img_data, np.uint8)
        if len(img_array.shape) == 2:
            img_array = np.stack([img_array] * 3, 2)
        cv2_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return cv2_img

    @staticmethod
    def get_plate_color(card_img):
        """获取行程卡颜色"""
        card_img_hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
        row_num, col_num = card_img_hsv.shape[:2]
        card_img_count = row_num * col_num
        green = yellow = red = 0
        for i in range(row_num):
            for j in range(col_num):
                H = card_img_hsv.item(i, j, 0)
                S = card_img_hsv.item(i, j, 1)
                V = card_img_hsv.item(i, j, 2)
                if 11 < H <= 34 and S > 34:
                    yellow += 1
                elif 35 < H <= 99 and S > 34:
                    green += 1
                elif (H < 10 or 156 < H <= 180) and S > 34:
                    red += 1

        color = "green"
        cololist = [green, yellow, red]

        i = cololist.index(max(cololist))
        if i == 0:
            color = "green"
        elif i == 1:
            color = "yellow"
        elif i == 2:
            color = "red"
        return color

    def distinguish(self, result, rect_img):
        """识别结果"""
        result = [i[1][0] for i in result]

        color_str = ""
        colorflg = False
        numchar = []
        extnum = ""
        reached_city = ""
        phone = ""
        time_str = ""
        status = f"正常"
        for i, res in enumerate(result):
            if i == 0:
                if f"绿" not in res:
                    color = self.get_plate_color(rect_img[0:10, :])
                    if color == "green":
                        color_str = f"请收下绿色行程卡"
                        colorflg = True
                    elif color == "yellow":
                        color_str = f"请收下黄色行程卡"
                        colorflg = False
                    else:
                        color_str = f"请收下红色行程卡"
                        colorflg = False
                else:
                    color_str = f"请收下绿色行程卡"
                    colorflg = True

            if len(numchar) < 2:
                strsub = re.findall(r"[0-9]+", res)
                if strsub:
                    strs = "".join(strsub)
                    if len(strs) > 5:
                        numchar.append(strs)
                        continue

            if len(numchar) == 2:
                strsub = re.findall(r"[0-9]+", result[i])
                if strsub:
                    strs = "".join(strsub)
                    if len(strs) > 5:
                        extnum = strs
                        continue

                strs = "".join([k for k in result[i:]])

                if "*" in strs or not colorflg:
                    status = f"异常"
                else:
                    status = f"正常"

                offs = strs.find("(")
                if offs > 0:
                    strs = strs[:offs]
                else:
                    offs = strs.find("注")
                    if offs > 0:
                        strs = strs[:offs]

                offs = strs.find(":")
                if offs > 0:
                    strs = strs[offs + 1 :]
                else:
                    offs = strs.find("经")
                    if offs > 0:
                        strs = strs[offs + 1 :]

                reached_city = f"您于前14天内到达或途经: " + strs.strip()
                break
        if len(numchar) == 2:
            str1 = numchar[0]
            phone = str1[:3] + "****" + str1[-4:]
            str2 = numchar[1]
            if len(str2) < 10:
                str2 += extnum
            time_str = str2[-14:]

        return {
            "color": color_str,
            "phone": phone,
            "time": time_str,
            "reached_city": reached_city,
            "status": status,
        }

    @staticmethod
    def shape_detect(image):
        h, w = image.shape[:2]
        rate = 500 / w
        _cv_img = cv2.resize(
            image, (0, 0), fx=rate, fy=rate, interpolation=cv2.INTER_CUBIC
        )

        gray = cv2.cvtColor(_cv_img, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 60, 60)

        contours, _ = cv2.findContours(
            edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        rect = None
        for c in contours:
            area = cv2.contourArea(c)
            if area < 15000:
                continue

            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.05 * peri, True)
            if len(approx) > 3:

                [x, y, w, h] = cv2.boundingRect(approx)
                rect = _cv_img[y : y + h, x + 5 : x + w - 5]

                circles = cv2.HoughCircles(
                    gray[y : y + h, x + 5 : x + w - 5], cv2.HOUGH_GRADIENT, 1.2, 100
                )
                if circles is not None:
                    circles = np.round(circles[0, :]).astype("int")
                    for (cx, cy, cr) in circles:
                        if abs(cx - w / 2) < 10:
                            img0 = rect[: cy - cr - 15, :]
                            img1 = rect[cy + cr + 15 :, :]
                            return np.vstack((img0, img1))

        return rect

    def run(self, image):
        """入口"""
        # cv_image = cv2.imread(self.base64_to_image(image))
        cv_image = self.base64_to_image(image)
        # shape_img = self.shape_detect(cv_image)
        ocr_text = self.ocr.ocr(img=cv_image, cls=True)
        return ocr_text
        # return self.distinguish(ocr_text, cv_image)


# if __name__ == '__main__':
#     ocr = PaddleOCR()
#     file_path = os.path.join(PaddleOCR.BASE_DIR, "image", "5.jpg")
#     with open(file_path, "rb") as f:
#         img = base64.b64encode(f.read())
#         print(img)
#         res = ocr.run(img)
#         print(res)

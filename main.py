import re
import time
import uvicorn
import cv2
import base64

from fastapi import FastAPI
from pydantic import BaseModel

from carddtv3 import detect_card
from paddle_ocr import PaddleOCR

app = FastAPI()

_ocr = PaddleOCR()


@app.get("/")
async def root():
    return {"message": "Hello World"}


class Item(BaseModel):
    pic: bytes


@app.post("/ocr")
async def ocr(item: Item):
    data = {"ocr_text": {}, "msg": "无法识别", "code": 200}
    res = _ocr.run(image=item.pic)

    if not res:
        data["code"] = 400
        return data
    data["ocr_text"] = res
    data["msg"] = "识别成功"
    return data


def distinguish(data):
    # data = {'ocr_text': [[[[[1210.0, 408.0], [1324.0, 425.0], [1313.0, 498.0], [1199.0, 481.0]], ['5C', 0.8048031330108643]], [[[776.0, 430.0], [952.0, 425.0], [954.0, 498.0], [778.0, 502.0]], ['李琴', 0.9988464117050171]], [[[791.0, 513.0], [938.0, 509.0], [939.0, 547.0], [792.0, 551.0]], ['产品经理', 0.9170127511024475]], [[[455.0, 640.0], [676.0, 640.0], [676.0, 704.0], [455.0, 704.0]], ['中国电信', 0.9959703683853149]],
    #                       [[[781.0, 642.0], [1373.0, 638.0], [1373.0, 671.0], [781.0, 675.0]], ['中国电信集团系统集成有限责任公司湖南分公司', 0.9358140826225281]], [[[779.0, 691.0], [1381.0, 687.0], [1382.0, 725.0], [779.0, 729.0]], ['中国电信股份有限公司湖南系统集成分公司', 0.9749830961227417]], [[[459.0, 705.0], [670.0, 705.0], [670.0, 731.0], [459.0, 731.0]], ['CHINA TELECOM', 0.910104513168335]], [[[779.0, 778.0], [1353.0, 774.0], [1353.0, 805.0], [779.0, 809.0]], ['地址：长沙市东二环1032号电信大楼37楼', 0.8925909399986267]],
    #                       [[[781.0, 818.0], [980.0, 818.0], [980.0, 849.0], [781.0, 849.0]], ['邮箱：410016', 0.9491695761680603]], [[[781.0, 856.0], [1069.0, 854.0], [1069.0, 887.0], [781.0, 889.0]], ['手机：15343013266', 0.9096843004226685]], [[[781.0, 898.0], [1198.0, 898.0], [1198.0, 929.0], [781.0, 929.0]], ['邮箱：15343013266@189.cn', 0.9416183233261108]]]], 'msg': '识别成功', 'code': 200}
    ocr_text = data.get("ocr_text")

    words_result = {
        "TITLE": [],
        "EMAIL": [],
        "ADDR": [],
        "COMPANY": [],
        "MOBILE": [],
        "NAME": [],
        "OTHER": [],
    }
    for item in ocr_text:  # for item in ocr_text[0]:
        text = item[1][0]
        if ("地址" in text) or ("号" in text) or ("楼" in text):
            addr = text.split("：")[-1]
            words_result["ADDR"].append(addr)
        elif "公司" in text:
            words_result["COMPANY"].append(text)
        elif ("经理" in text) or ("师" in text):
            words_result["TITLE"].append(text)
        elif len(text) in [2, 3]:
            words_result["NAME"].append(text)
        elif re.findall(
            r"[a-zA-Z]?[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}", text, re.S
        ):
            _ = re.findall(
                r"[a-zA-Z]?[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}", text, re.S
            )
            words_result["EMAIL"].extend(_)
        elif re.findall(r"(?:\D|^)(1[3456789]\d{9})(?:\D|$)", text):
            _ = re.findall(r"(?:\D|^)(1[3456789]\d{9})(?:\D|$)", text)
            words_result["MOBILE"].extend(_)
        else:
            words_result["OTHER"].append(text)
    _data = {
        "words_result_num": len(words_result.keys()),
        "words_result": words_result,
        "log_id": str(time.time_ns()),
    }
    return _data


@app.post("/ocr_card")
async def ocr(item: Item):
    data = {"ocr_text": {}, "msg": "无法识别", "code": 200}
    image = item.pic

    # 裁剪，保持base64格式
    cv2_image = PaddleOCR.base64_to_image(image)
    crop_image = detect_card(cv2_image)
    if crop_image is not None:  # 处理None,裁剪成功则用,否则用原图
        base64_str = cv2.imencode(".jpg", cv2_image)[1].tobytes()
        image = base64.b64encode(base64_str)

    # 解析文字
    res = _ocr.run(image=image)

    if not res:
        data["code"] = 400
        return data
    data["ocr_text"] = res
    data["msg"] = "识别成功"

    data["ocr_text"] = distinguish(data)
    data["image"] = image
    return data


if __name__ == "__main__":
    uvicorn.run(
        app="main:app", host="0.0.0.0", port=8008, reload=True, debug=True, workers=4
    )

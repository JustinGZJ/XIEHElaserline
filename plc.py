from logger import logger as logging
import requests


def write_plc(address, value):
    # 写入plc
    url = f'http://127.0.0.1:1880/plc/set'
    data = {'address': address, 'value': value}
    response = requests.post(url=url, data=data)
    if response.status_code == 200:
        logging.debug(f"{address}:{value}写入成功")
        return True
    else:
        logging.debug(f"{address}:{value}写入失败")
        return False

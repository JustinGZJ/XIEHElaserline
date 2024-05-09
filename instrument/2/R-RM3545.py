import pyvisa as visa
from plc import write_plc
import time
from logger import logger as logging


rm3545_resouce = '''ASRL2::INSTR'''
relay_delay =2

TestItems = [
    {
        "Name": "DC+ - DC+'",
        "Category": "Resistance",
        "Lower": 0.060,
        "Upper": 0.19,
        "Unit": "mOhm"
    },
    {
        "Name": "DC- - DC-'",
        "Category": "Resistance",
        "Lower": 0.085,
        "Upper": 0.2,
        "Unit": "mOhm"
    }
]


def connect_device(resource):
    # 创建一个资源管理器
    rm = visa.ResourceManager()
    # 连接到指定的设备
    device = rm.open_resource(resource)
    # 判断连接是否成功
    if device.query('*IDN?') == '':
        logging.debug("连接失败")
    else:
        logging.debug("连接成功")
    # 返回设备对象
    return device


def close_device(device):
    # 关闭与仪器的连接
    device.close()


def config(device):
    device.write('*RST;*CLS;')
    # device.write(':SYST:LFR 50;')
    
    # device.write(':SENS:FUNC RES;')
    # device.write(':RES:RANG 1.00E-3;')
    # device.write(':SAMP:RATE SLOW1;')
    device.write(':INIT:CONT ON;')


def measure(device):
    # 开始测量,等待测量完成
    result = device.query('Fetch?')
    return result



def main():
    # 连接设备
    device = connect_device(rm3545_resouce)
    plc_step_address = 'D6085'
    # 收到后把D5085/D6086 置0
    write_plc('D5085', 0)
    write_plc('D6086', 0)

    write_plc(plc_step_address, 0)
    
    # 配置设备
    config(device)
    time.sleep(relay_delay)
    # 测量DC+-DC+'的电阻值
    result = measure(device)
    result = float(result) * 1000
    TestItems[0]["Value"]=result
    if TestItems[0]["Lower"] < result < TestItems[0]["Upper"]:
        TestItems[0]["Result"] = "PASS"
    else:
        TestItems[0]["Result"] = "FAIL"
    logging.debug(result)
    write_plc(plc_step_address, 1)

    time.sleep(relay_delay)
    # 测量DC--DC-'的电阻值
    result = measure(device)
    result = float(result) * 1000
    TestItems[1]["Value"]=result
    if TestItems[1]["Lower"] < result < TestItems[1]["Upper"]:
        TestItems[1]["Result"] = "PASS"
    else:
        TestItems[1]["Result"] = "FAIL"
    logging.debug(result)
    write_plc(plc_step_address, 2)
    time.sleep(relay_delay)
    write_plc(plc_step_address, 10)
    final_result="PASS"
    # 如果有失败项，则向PLC写入PLC D6086 写入2，如果全部PASS则写入1
    if "FAIL" in [item["Result"] for item in TestItems]:
        write_plc("D6086", 2)
        final_result="FAIL"
    else:
        write_plc("D6086", 1)
        final_result="PASS"

    # 关闭设备
    close_device(device)
    return {
        "Name":"电阻测试",
        "Result":final_result,
        "TestItems":TestItems
        }


if __name__ == "__main__":
  print(main())

# *RST;
# *CLS;
# :SYST:LFR 50;
# :SENS:FUNC RES;
# :RES:RANG 1.00E-3;
# :SAMP:RATE SLOW1;
# :INIT:CONT ON;
# :TRIG:SOUR IMM

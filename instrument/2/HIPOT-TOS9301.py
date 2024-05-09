import pyvisa
import time
import requests
from logger import logger as logging
from plc import write_plc

tos9301_resouce = '''TCPIP0::192.168.1.103::inst0::INSTR'''
# 数据读取时间延迟
delay=4

# 测试项目列表
TestItems = [
    {
        "Name": "IR",
        "Category": "IR",
        "Lower": 100,
        "Upper": 1000000,
        "Unit": "MOhm"
    },
    {

        "Name": "DC+ - DC-",

        "Category": "DCW",

        "Lower": 0,

        "Upper": 10,

        "Unit": "mA"

    },
    {
        "Name": "DC+&DC- - GND",

        "Category": "DCW",

        "Lower": 0,

        "Upper": 10,

        "Unit": "mA"
    }
]
def get_test_status(device):
    """
    获取测试状态
    :param device: 设备对象
    :return: 测试状态字典
    """
    # 发送查询命令
    response = device.query('STAT:OPER:TEST:COND?\n').strip()
    print(response)
    response = response.lstrip('+-')
    # 确保响应是数字
    if response.isdigit():
        # 将字符串转换为整数
        response_int = int(response)
        # 拆解不同的位到一个字典中
        test_status = {
            'PASS': response_int & 1,
            'L-FAIL': (response_int >> 1) & 1,
            'U-FAIL': (response_int >> 2) & 1,
            'RESERVED-3': (response_int >> 3) & 1,
            'RISE': (response_int >> 4) & 1,
            'TEST': (response_int >> 5) & 1,
            'FAIL': (response_int >> 6) & 1,
            'DISCHARGE': (response_int >> 7) & 1,
            'READY': (response_int >> 8) & 1,
            'IDLE': (response_int >>9) & 1,
            'STOP': (response_int >> 10) & 1,
            'PROTECT': (response_int >> 11) & 1,
            'dV/dt FAIL': (response_int >> 12) & 1,
            'RESERVED-13': (response_int >> 13) & 1,
            'CONTACT-CHECK': (response_int >> 14) & 1,
            'RESERVED-15': (response_int >> 15) & 1,
        }
        return test_status
    raise ValueError('Invalid response: {}'.format(response))

def get_test_result(device):
    """
    获取测试结果
    :param device: 设备对象
    :return: 测试结果列表
    """
    results=[]
    while True:
        response = device.query('RES:REM?\n').strip()
        if response=='+0':
            break
        print(response)
        # 解析并存储测试结果
        result = {
            'NUM': response.split(',')[0],
            'STEP': response.split(',')[1],
            'FUNC': response.split(',')[2],
            'YEAR': response.split(',')[3],
            'MONTH': response.split(',')[4],
            'DAY': response.split(',')[5],
            'HOUR': response.split(',')[6],
            'MIN': response.split(',')[7],
            'SEC': response.split(',')[8],
            'VOLT': response.split(',')[9],
            'CURR': response.split(',')[10],
            'RES': response.split(',')[11],
            'ETIM': response.split(',')[12],
            'JUDG': response.split(',')[13],
        }
        results.append(result)        
    return results
    
def wait_for_test_complete(device, timeout=20):
    """
    等待测试完成
    :param device: 设备对象
    :param timeout: 超时时间（秒）
    :return: 测试是否完成
    """
    start_time = time.time()
    while True:
        status = get_test_status(device)
        if status["IDLE"]==1:
            return True
        elif time.time() - start_time > timeout:
            return False
        time.sleep(1)
        print("Test is still running...")
            


def connect_device(resource):
    """
    连接设备
    :param resource: 设备资源地址
    :return: 设备对象
    """
    # 创建一个资源管理器
    rm = pyvisa.ResourceManager()
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
    """
    关闭设备连接
    :param device: 设备对象
    """
    # 关闭与仪器的连接
    device.close()


def check_protect(device):
    """
    检查保护状态
    :param device: 设备对象
    :return: 是否处于保护状态
    """
    protect_condition = device.query('STATus:OPERation:PROTecting:CONDition?').strip()
    if protect_condition == '0':
        logging.debug("没有保护条件")
    else:
        logging.debug("有保护条件")
    return protect_condition == "0"


def measure(resource,param={"program":'3477'}):
    """
    对设备进行测量
    :param resource: 设备资源地址
    :param param: 测量参数字典，包括程序名
    :return: 测量结果
    """
    device = connect_device(resource)
    device.write("*RST;*CLS;")
    device.write(f'PROG "/BASIC/{param["program"]}"')
    device.write('INIT:TEST')
    get_test_result(device)
    time.sleep(1)
    wait_for_test_complete(device)
    result=get_test_result(device)
    return result

def main():
    """
    主程序，控制测试流程
    """
    write_plc("D5050", 0)     # 清除请求信号
    write_plc("D6050", 0)     # 清除完成信号
    results=measure(resource=tos9301_resouce)
    final_result="PASS"
    # 如果所有结果都是PASS,则写入完成信号
    if all(result["JUDG"] == "PASS" for result in results):
        final_result="PASS"
        write_plc("D6051", 1)
    else:
        final_result="FAIL"
        write_plc("D6051", 0)
    write_plc("D6050", 1)      # 置位完成信号
    # 把测试结果和测试值写入testitems 顺序写入
    for i, result in enumerate(results):
        TestItems[i]["Result"]=result["JUDG"]
        if result["FUNC"]=="DCW":
            TestItems[i]["Value"]=float(result["CURR"])*1000
        if result["FUNC"]=="IR":
           TestItems[i]["Value"]=float(result["RES"])/1000000
    return {
        "Name":"耐压测试",
        "Result":final_result,
        "TestItems":TestItems
        }

if __name__ == '__main__':
    print(main())


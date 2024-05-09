import pyvisa as visa
from plc import write_plc
import time
from logger import logger as logging
TestItems = [
    {
        "Name": "DC+ - DC+'",
        "Category": "Inductance",
        "Lower": 14,
        "Upper": 26,
        "Unit": "uH"
    },
    {
        "Name": "DC- - DC-'",
        "Category": "Inductance",
        "Lower": 14,
        "Upper": 26,
        "Unit": "uH"
    },
    {
        "Name": "DC+ - DC-",
        "Category": "Capacitance",
        "Lower": 960,
        "Upper": 1440,
        "Unit": "nF"
    },
    {
        "Name": "DC+ - GND",
        "Category": "Capacitance",
        "Lower": 542,
        "Upper": 813,
        "Unit": "nF"
    },
    {
        "Name": "DC- - GND",
        "Category": "Capacitance",
        "Lower": 542,
        "Upper": 813,
        "Unit": "nF"
    }
]
# e4890_resouce= '''USB0::0x2A8D::0x2F01::MY46624897::INSTR'''
e4890_resouce = '''USB0::0x2A8D::0x2F01::MY46624897::INSTR'''
relay_delay = 0.2


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



# 校准
def calibration(mode):
    try:
        device = connect_device(e4890_resouce)
        # mode 选择开路校准和短路校准
        if mode == 'OPEN':
            device.write(':CORR:OPEN')
        elif mode == 'SHORT':
            device.write(':CORR:SHOR')
        else:
            logging.debug("校准模式错误")
        return "校准成功:"+mode
    except:
        return "校准连接失败"
    finally:
        close_device(device)



def config_ls(device,freq,voltage):
    # 设置测量功能为电感和串联电阻
    device.write(':FUNC:IMP:TYPE LSRS')
    # 打开自动测量范围
    device.write(':FUNC:IMP:RANG:AUTO ON')
    # 设置测量范围为100欧姆
    device.write(':FUNCtion:IMPedance:RANGe 100;')
    # 设置频率10k
    device.write(f':FREQ {freq};')
    # 设置电压
    device.write(f':VOLT {voltage}')
    # 设置电流10mA
    device.write(':CURR 10;')
    # 设置速度和分辨率
    device.write(':APERture MED,1')


def config_cap(device,freq,voltage):
    # 设置测量功能为电容和并联电阻
    device.write(':FUNC:IMP:TYPE CPD')
    # 打开自动测量范围
    device.write(':FUNC:IMP:RANG:AUTO ON')
    # 设置测量范围为100欧姆
    device.write(':FUNCtion:IMPedance:RANGe 100;')
    # 设置频率1khz
    device.write(f':FREQ {freq};')
    # 设置电压
    device.write(f':VOLT {voltage};')
    # 设置速度和分辨率
    device.write(':APERture MED,1')


def measure(device):
    # 开始测量
    device.write(':INIT')
    # 等待测量完成
    device.query('*OPC?')
    # 读取测量结果
    result = device.query(':FETC?')
    return result


def main():
    plc_step_addr = "D6080"
    # 清除 D5080/D6081 D6082
    write_plc('D5080', 0)
    write_plc('D6081', 0)
    write_plc('D6082', 0)
    # 连接设备
    device = connect_device(e4890_resouce)
    write_plc(plc_step_addr, 0)
    # 测量电感 DC+ - DC+'
    config_ls(device,100000,0.1)
    result = measure(device)
    print(result)
    logging.debug(result + '\n')
    # -1.22084E+02,+9.47753E+05,+0 提取电感值
    result = result.split(',')
    result = float(result[0]) * 1000000
    TestItems[0]['Value'] = result

    # 根据上下限判断是否合格
    if TestItems[0]['Lower'] < result < TestItems[0]['Upper']:
        TestItems[0]['Result'] = 'PASS'
    else:
        TestItems[0]['Result'] = 'FAIL'
    write_plc(plc_step_addr, 1)
    time.sleep(relay_delay)

    # 测量电感 DC- - DC-'
    config_ls(device,100000,0.1)
    result = measure(device)
    logging.debug(result)
    print(result + '\n')

    # -1.22084E+02,+9.47753E+05,+0 提取电感值
    result = result.split(',')
    result = float(result[0]) * 1000000
    TestItems[1]['Value'] = result

    # 根据上下限判断是否合格
    if TestItems[1]['Lower'] < result < TestItems[1]['Upper']:
        TestItems[1]['Result'] = 'PASS'
    else:
        TestItems[1]['Result'] = 'FAIL'

    write_plc(plc_step_addr, 2)
    time.sleep(relay_delay)

    # 测量电容 DC+ - DC-
    config_cap(device,1000,1)
    result = measure(device)
    logging.debug(result)
    print(result + '\n')
    write_plc(plc_step_addr, 3)
    time.sleep(relay_delay)

    # -1.22084E+02,+9.47753E+05,+0 提取电感值
    result = result.split(',')
    result = float(result[0]) * 1000000000
    TestItems[2]['Value'] = result

    # 根据上下限判断是否合格
    if TestItems[2]['Lower'] < result < TestItems[2]['Upper']:
        TestItems[2]['Result'] = 'PASS'
    else:
        TestItems[2]['Result'] = 'FAIL'

    # 测量电容 DC+ - gnd
    config_cap(device,1000,1)
    result = measure(device)
    logging.debug(result)
    print(result + '\n')
    write_plc(plc_step_addr, 4)
    time.sleep(relay_delay)
    # -1.22084E+02,+9.47753E+05,+0 提取电感值
    result = result.split(',')
    result = float(result[0]) * 1000000000
    TestItems[3]['Value'] = result

    # 根据上下限判断是否合格
    if TestItems[3]['Lower'] < result < TestItems[3]['Upper']:
        TestItems[3]['Result'] = 'PASS'
    else:
        TestItems[3]['Result'] = 'FAIL'

    # 测量电容 DC- - gnd
    config_cap(device,1000,1)
    result = measure(device)
    logging.debug(result + '\n')
    write_plc(plc_step_addr, 5)
    print(result)
    logging.debug(result)

    # -1.22084E+02,+9.47753E+05,+0 提取电感值
    result = result.split(',')
    result = float(result[0]) * 1000000000
    TestItems[4]['Value'] = result

    # 根据上下限判断是否合格
    if TestItems[4]['Lower'] < result < TestItems[4]['Upper']:
        TestItems[4]['Result'] = 'PASS'
    else:
        TestItems[4]['Result'] = 'FAIL'
    # 通知完成测试
     
    # 输出结果
    # 如果testitems[0] 和 testitems[1] 都是PASS,则给PLC写1，否则写2
    if TestItems[0]['Result'] == 'PASS' and TestItems[1]['Result'] == 'PASS':
        write_plc("D6081", 1)
    else:
        write_plc("D6081", 2)
    # 如果testitems[2] 和 testitems[3] 和 testitems[4] 都是PASS,则给PLC写1，否则写2
    if TestItems[2]['Result'] == 'PASS' and TestItems[3]['Result'] == 'PASS' and TestItems[4]['Result'] == 'PASS':
        write_plc("D6082", 1)
    else:
        write_plc("D6082", 2)

    write_plc(plc_step_addr, 10)
    final_result='PASS'
    # 关闭设备
    if all(item['Result'] == 'PASS' for item in TestItems):
        final_result='PASS'   
    else:
        final_result='FAIL'
    close_device(device)
    return {
        "Name":"LC",
        "Result": final_result,
        "TestItems":TestItems}


if __name__ == '__main__':
    #result = calibration("OPEN")
    result=main()
    print(result)


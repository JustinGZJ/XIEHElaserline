import pyvisa as visa
import matplotlib.pyplot as plt
import niswitch
import logging
import time
import numpy as np
import requests

logging.basicConfig(level=logging.DEBUG, filemode='w', filename="znl.log",
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
znl_resouce = '''TCPIP0::192.168.1.16::inst0::INSTR'''

frequency = [10, 30, 60, 100, 200, 300, 350, 430, 550, 600, 800, 1000, 2000, 5000, 10000, 30000, 40000, 50000, 60000,
             80000, 100000]

l1_lower = [12, 21, 28, 32, 39, 39, 45, 45, 53, 52, 48, 45, 41, 36, 33, 32, 33, 42, 35, 27, 20]
l1_upper = [18, 28, 36, 42, 63, 60, 67, 85, 85, 78, 78, 79, 71, 60, 50, 55, 64, 64, 55, 50, 46]

l2_lower = [12, 21, 27, 32, 39, 44, 48, 49, 49, 48, 47, 45, 40, 37, 34, 30, 35, 40, 35, 26, 20]
l2_upper = [18, 28, 36, 42, 55, 63, 85, 85, 85, 70, 80, 80, 65, 55, 52, 50, 65, 68, 70, 65, 50]


def connect_device(resource):
    # 创建一个资源管理器
    rm = visa.ResourceManager()
    # 连接到指定的设备
    device = rm.open_resource(znl_resouce)
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
    # 选择设备的通道1
    device.write('INST:SEL CHANNEL1;')
    # 设置设备的功能为S21功率传输
    device.write('SENS1:FUNC "XFR:POW:S21";')
    # 打开设备的显示更新
    device.write('SYST:DISP:UPD ON;')
    # 设置设备的计算格式为幅度
    device.write('CALC1:FORM MAGN;')
    # 设置设备的源功率级别为0dbm
    device.write('SOUR1:POW:LEV 0dbm;')
    # 设置设备的扫描空间为对数
    device.write('SENS1:SWE:SPAC LOG;')
    device.write('SENS1:SWE:TIME:AUTO ON;')
    device.write('SENS1:SWE:POIN 400;')
    device.write('SENS1:BAND:AUTO ON;')
    device.write('SENS1:BAND 1kHz;')
    device.write('DISP:WIND1:TRAC1:Y:SCAL:TOP 0dB;')
    device.write('DISP:WIND1:TRAC1:Y:SCAL:BOTT -120dB;')
    device.write('SENS1:DET:FUNC NORM;')
    # 设置设备的平均模式为点
    device.write('SENS1:AVER:MODE POIN;')
    # 设置设备的平均计数为2
    device.write('SENS1:AVER:COUN 2;')
    # 打开设备的平均功能
    device.write('SENS1:AVER ON;')
    # 设置设备的源功率级别为0dbm
    device.write('SOUR1:POW:LEV 0dbm;')
    # 设置设备的带宽为1kHz
    device.write('SENS1:BAND 300Hz;')
    # 设置设备的频率起始值为10kHz
    device.write('SENS1:FREQ:START 10 kHz;')
    # 设置设备的频率结束值为100000kHz
    device.write('SENS1:FREQ:STOP 100000 kHz;')
    # 清除设备的所有段
    device.write('SENS1:SEGM:CLE;')

    # 为每个频率点定义一个频率段
    for i, freq in enumerate(frequency):
        device.write(f'SENS1:SEGM:DEF{i + 1} {freq}kHz,{freq}kHz,1,0dBm,AUTO,2,300 Hz;')

    # 设置设备的频率模式为段
    device.write('SENS1:FREQ:MODE SEGM;')


def get_data(device):
    # 打开设备的显示更新
    device.write('SYST:DISP:UPD ON')
    # 关闭设备的错误显示
    # 关闭设备的自动扫描时间
    device.write('SENS1:SWE:TIME:AUTO OFF')
    # 设置设备的扫描时间为1秒
    device.write('SENS1:SWE:TIME 1')
    # 设置设备的计算格式为对数幅度
    device.write('CALC1:FORM MLOG')
    # 设置设备的图形显示范围为10dB
    device.write('CALC1:GDAP:SCO 10')
    # 设置设备的扫描点数为100
    device.write('SWE:POIN 100')
    # 设置设备的损失补偿值为-12dB
    device.write('CORRection:LOSS:OFFSet 0')
    # 设置设备的频率起始值为10000Hz
    # 设置设备的频率起始值为10000Hz
    device.write('FREQuency:STARt 10000')
    # 设置设备的频率结束值为60000000Hz
    device.write('FREQ:STOP 10000000')
    # 打开设备的连续初始化模式
    device.write('INIT:CONT:ALL ON')
    # 设置设备的扫描次数为1
    device.write('SWE:COUN:ALL 1')
    # 设置设备的初始化范围为全部
    device.write('INIT1:SCOP ALL')
    # 触发设备开始初始化，并等待初始化完成
    device.write('INIT1;*OPC')

    # 对于查询命令，我们需要读取返回的数据
    data_format =np.abs(device.query_binary_values('FORMAT REAL,32;:CALC:DATA:DALL? FDAT'))
    trace_data = device.query_binary_values('TRAC:STIM? CH1DATA')
    # 打印接收的数据
    logging.debug(data_format)
    logging.debug(trace_data)
    return data_format, trace_data


def plot_data(data_format, trace_data, channel=1):
    plt.plot(trace_data, data_format)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.xscale('log')
    # 添加上下限制
    if channel == 1:
        plt.plot(trace_data,l1_lower , 'r--')
        plt.plot(trace_data,l1_upper, 'r--')
    else:
        plt.plot(trace_data,l2_lower,  'r--')
        plt.plot(trace_data,l2_upper,  'r--')
    # 保存图片，按照当前时间命名
    plt.savefig(f'loss-channel{channel}.png')
    plt.close()

def switch_channel(channel=1, resource='TCPIP::192.168.48.147::INSTR'):
    rm = visa.ResourceManager()
    try:
        instrument = rm.open_resource(resource)
        commands = []

        if channel == 1:
            commands = [
                'ROUTE:CLOSE (@F01A11(0101))',
                'ROUTE:CLOSE (@F01A11(0102))',
                'ROUTE:CLOSE (@F01A12(0001))',
                'ROUTE:CLOSE (@F01A12(0002))',
                'ROUTE:CLOSE (@F01A13(0101))',
                'ROUTE:CLOSE (@F01A13(0102))'
            ]
        elif channel == 2:
            commands = [
                'ROUTE:CLOSE (@F01A11(0001))',
                'ROUTE:CLOSE (@F01A11(0002))',
                'ROUTE:CLOSE (@F01A12(0101))',
                'ROUTE:CLOSE (@F01A12(0102))',
                'ROUTE:CLOSE (@F01A13(0201))',
                'ROUTE:CLOSE (@F01A13(0202))'
            ]
        
        # Send commands one by one
        for cmd in commands:
            instrument.write(cmd)
            # Optionally add a delay or read back responses where necessary
            # response = instrument.read()  # if feedback is needed
            # print(response)

    except visa.VisaIOError as e:
        print(f"Error communicating with the device: {e}")
    finally:
        # Ensures that the connection is closed even if an error occurs
        if 'instrument' in locals():
            instrument.close()


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


def create_data_point(i, j, freq, data_format):
    lower = l1_lower if i == 1 else l2_lower
    upper = l1_upper if i == 1 else l2_upper
    category = "Loss-1" if i == 1 else "Loss-2"
    return {
        "Name": freq,
        "Category": category,
        "Lower": lower[j],
        "Upper": upper[j],
        "Value":data_format[j],
        "Result": "PASS" if lower[j] <data_format[j] < upper[j] else "FAIL",
        "Unit": "dB"
    }


def measure():
    try:
        device = connect_device(znl_resouce)
        config(device)
        data = []
        for i in range(1, 3):
            switch_channel(i)
            time.sleep(0.5)  # consider replacing this with a more dynamic wait
            data_format, trace_data = get_data(device)
            #data.append((data_format, trace_data))
            #plot_data(data_format, trace_data, i)
            for j, freq in enumerate(frequency):
                data_point = create_data_point(i, j, freq, data_format)
                data.append(data_point)
        close_device(device)
        return data
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return []


def main():
    write_plc("D5120", 0)
    write_plc("D6121", 0)
    result = measure()
    results=[item["Result"] for item in result]
    final_result="PASS"
    if "FAIL" in results:
        write_plc("D6121", 2)
        final_result="FAIL"
    else:
        write_plc("D6121", 1)
        final_result="PASS"
    write_plc("D6120", 10)
    return {
        "Name":"Loss",
        "Result":final_result,
        "TestItems":result
    }


if __name__ == "__main__":
    print(main())

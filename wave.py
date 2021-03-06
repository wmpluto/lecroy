# -*- coding: utf-8 -*-

from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
import sys, getopt

class Wave:
    analog = []
    digital = []
    data_type = 0

    def __init__(self, file_path, sample_frequency=50000000, data_rate=4000, code='MAN', div=100):
        self.fs = sample_frequency
        self.ds = data_rate
        self.div = div
        self.code = code
        self.deltat = 1/self.fs

        self.readdata(file_path)

    def readdata(self, path):
        with open(path, 'r') as file:
            # get sample frequency from file
            self.deltat = 0
            for i in range(0, 15):
                line = file.readline()
                if i == 10 or i == 11:
                    self.deltat = float(line.split(',')[0]) - self.deltat
            self.fs = int(1/self.deltat)
            print("frequency: ", self.fs)

            i = 0
            for line in file.readlines():
                try:
                    if i % self.div == 0:
                        self.analog.append(float(line.split(',')[1]))
                    i += 1
                except:
                    pass

        self.data_type = 0
        return self

    def makezero(self):
        mean = np.mean(self.analog)
        self.analog = [abs(i-mean) for i in self.analog]

        self.data_type = 0
        return self

    def lowpass(self, order=1, btype='lowpass'):
        wn = round(1.0 * self.ds / (self.fs/2) * self.div, 5)
        b, a = signal.butter(order, wn)
        self.analog = signal.filtfilt(b, a, self.analog)

        self.data_type = 0
        return self

    def digitize(self):
        # set mean as trigger value
        mean = np.mean(self.analog)
        self.analog = np.where(self.analog > mean, 1, 0)

        self.digital = self.analog
        dig = [self.digital[0]]
        cnt = [0]
        l = len(self.digital)
        window = self.fs / self.ds / self.div / (2 if self.code == 'MAN' else 1)
        print("window count: ", window)
        print("window time: %fms" % (window * self.div * self.deltat * 1000))
        for i in range(0, l):
            if self.digital[i] == dig[-1]:
                cnt[-1] += 1
            else:
                n = int(round(cnt[-1] / window)) - 1
                dig += n * [dig[-1]]
                cnt += n * [1]

                dig.append(self.digital[i])
                cnt.append(1) 
        print(cnt)
        self.digital = dig
        
        self.data_type = 1
        self.log()
        return self

    def locate(self, sfid='1001'):
        self.digital = self.digital[self.listtostr(self.digital).index(sfid)+len(sfid):]
        
        self.data_type = 1
        return self

    def decode(self, code='MAN'):
        if code != 'MAN':
            return self
        if self.code != 'MAN':
            return self

        data_str = self.listtostr(self.digital)
        self.digital = []

        l = len(data_str)
        for i in range(0, l // 2):
            if data_str[i*2:i*2+2] == '10':
                self.digital.append(0)
            elif data_str[i*2:i*2+2] == '01':
                self.digital.append(1)
            else:
                print("MAN Decode Error")

        self.data_type = 1
        return self

    def bittohex(self):
        self.digital = self.digital[0: 4 * (len(self.digital) // 4)]
        
        self.data_type = 1
        return hex(int(self.listtostr(self.digital),2))

    def log(self):
        if self.data_type:
            print(self.listtostr(self.digital))

    def listtostr(self, l):
        return ''.join([str(i) for i in l])

def main():
    file_path = 'test.csv'
    sample_frequency = 50000000
    data_rate = 4000
    code = 'MAN'
    sfid = '1001'
    div = 100
    rf = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:", ["rf", "lf", "sf=","dr=","help", "code=","sfid=","div="])
    except getopt.GetoptError as err:
        print("error input")
        return

    for o, a in opts:
        if o in ("-h", "--help"):
            print("wave.py -f file_path --sf sample_frequency --dr data_rate --code MAN --sfid 10 --div 100 --lf")
            sys.exit()
        elif o in ("-f"):
            file_path = a
        elif o in ("--sf"):
            sample_frequency = int(a)
        elif o in ("--dr"):
            data_rate = int(a)
        elif o in ("--code"):
            code = a
        elif o in ("--div"):
            div = int(a)
        elif o in ("--sfid"):
            sfid = a
        elif o =="--lf":
            rf = 0
        elif o =="--rf":
            rf = 1            
        else:
            assert False, "unhandled option"

    if rf:
        print(Wave(file_path, sample_frequency, data_rate, code, div)\
                #.makezero()\
                #.lowpass()\
                .digitize()\
                .locate(sfid)\
                .decode()\
                .bittohex()
                )
    else:
        plt.figure
        original_wave = Wave(file_path, sample_frequency, data_rate, code, div)
        plt.plot(original_wave.analog, 'b')
        analog_wave = original_wave\
                .makezero()\
                .lowpass()
        plt.plot(analog_wave.analog, 'y')
        digital_wave = analog_wave.digitize()\
                .locate(sfid)\
                .decode()
        plt.plot(analog_wave.analog, 'r')
        print(digital_wave.bittohex())
        plt.grid(True)
        plt.show()

if __name__ == '__main__':
    main()
 

#v3 - 26 Sep 2019

import requests
from time import sleep 
import os
import datetime
import subprocess

def get_gpu_info(param):
   try:
      sp = subprocess.Popen(['nvidia-smi', '--query-gpu=temperature.gpu,fan.speed,power.draw', '--format=csv,noheader'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out_str = sp.communicate()
      out_list = out_str[0].split(b'\r\n')
      final_list = []
      for item in out_list:
          temp = str(item).split("'")[1]
          if temp != '':
              final_list.append(temp)

      #closing subprocess
      sp.kill()

      gpu_count = len(final_list)
      temp_list = []
      fan_list = []
      power_list = []

     
      for i in range(gpu_count):
         out = final_list[i].split(", ")
         try:
            temp_list.append(int(float(out[0])))
         except:
            temp_list.append(-1)

         try:
            fan_list.append(int(float(out[1].split(" ")[0])))
         except:
            fan_list.append(-1)

         try:
            power_list.append(int(float(out[2].split(" ")[0])))
         except:
            power_list.append(-1)

      if param == "temp":
          return temp_list
      elif param == "fan":
          return fan_list
      elif param == "power":
          return power_list
      elif param == "all":
          return temp_list, fan_list, power_list
   except:
      return []

def get_hashes_from_bminer():
   try:
      hashrates = []
      r = requests.get('http://127.0.0.1:1880/api/v1/status/solver')
      json = r.json()
      results = json['devices']
      rates = []
      gpu_count, gpu_list = get_gpu_count_from_bminer()
      if gpu_count != -1:
         for i in gpu_list:
            #for eth
            rate = results['{}'.format(str(i))]['solvers'][0]['speed_info']['hash_rate']
            rate = int(float(rate)/1000000)

            #for zec
            #rate = results['{}'.format(str(i))]['solvers'][0]['speed_info']['solution_rate']
            #rate = int(float(rate))

            rates.append(rate)
      else:
         return []
      return rates, gpu_list
   except:
      return []
   
def get_gpu_count_from_bminer():
   try:
      r = requests.get('http://127.0.0.1:1880/api/v1/status/solver')
      json = r.json()
      results = json['devices']
      return len(results), list(results.keys())
   except:
      return -1 

def restart_bMiner():
   os.system("taskkill /f /im  bminer.exe")
   sleep(5)
   os.chdir("path_to_miner_folder")
   os.startfile("mine.bat")
   sleep(15)

print('will start miner check within 15 sec...')
sleep(15)
os.environ['NO_PROXY'] = '127.0.0.1'
while True:
   try:
      hashrates, gpu_list = get_hashes_from_bminer()
      temps, fans, powers = get_gpu_info('all')
      print('number of GPUs: {}'.format(len(hashrates)))
      #print('number of temps: {}'.format(len(temps)))
      #print('number of powers: {}'.format(len(powers)))
      #print('number of fans: {}'.format(len(fans)))

      print('Total hashrate: {}'.format(sum(hashrates)))

      if len(hashrates) > 0 and sum(hashrates) > 0:
         # hashrates -> [20,20,20,20], gpu_list -> [1,2,3,4] when GPU0 is turned off in the miner
         # transformin above line to hashrates -> [-1,20,20,20,20,-1]
         for i in range(6):
            if i not in gpu_list:
               if i < int(gpu_list[0]): #then we should use insert command
                  hashrates.insert(i,-1)
               elif i > int(gpu_list[-1]): #-1 is the last element, then we should use append command
                  hashrates.append(-1)

         if len(temps) < len(hashrates):
            for i in range(6 - len(temps)):
               temps.append(-1)
               powers.append(-1)
               fans.append(-1)

         for i in range(6):
            print('GPU{}: {}, temp: {}, fan: {}'.format(i, hashrates[i], temps[i], fans[i]))

         try:
            post_data = {}
            post_data['miner'] = 'miner_name'
            for i in range(6):
               post_data['gpu{}'.format(i)] = hashrates[i]
               post_data['gpu{}temp'.format(i)] = temps[i]
               post_data['gpu{}power'.format(i)] = powers[i]
               post_data['gpu{}fan'.format(i)] = fans[i]
            post_data['pytime'] = datetime.datetime.utcnow()

            r2 = requests.post("your_server_url", data = post_data)
            print(r2.status_code, r2.reason)
         except:
            print('Error sending data to the server')

      sleep(20)
   except:
      print('error getting data from miner, will try again in 10 sec...')
      sleep(10)

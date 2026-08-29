from machine import Pin, ADC, PWM, I2C
import time
import network
import urequests
from tm1637 import TM1637
from ssd1306 import SSD1306_I2C
import ntptime

# 定義接腳
BUZZER_PIN = 32
AO_PIN = 34
SERVO_PIN = 27
BUTTON_PIN = 33
SCL_PIN = 22
SDA_PIN = 21

# Wi-Fi 配置
SSID = "11146078"
PASSWORD = "11146078wifi"
NODE_RED_URL = "http://192.168.1.102:1880/score"  # 替換為您的 Node-RED 地址

# 初始化蜂鳴器
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.duty(0)  # 初始靜音

# 初始化伺服馬達
servo = PWM(Pin(SERVO_PIN), freq=50)

# 初始化光敏感測器
ao_sensor = ADC(Pin(AO_PIN))
ao_sensor.atten(ADC.ATTN_11DB)
ao_sensor.width(ADC.WIDTH_12BIT)

# 初始化按鈕
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# 初始化 TM1637 顯示器
tm = TM1637(clk=Pin(4), dio=Pin(5))

# 初始化 OLED 螢幕
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
oled = SSD1306_I2C(128, 64, i2c)

# 計分與計時
score = 0
start_time = 0
running = False  # 系統是否啟動
game_duration = 15  # 限時遊戲時間
time_left = game_duration  # 剩餘時間（秒）

# 防抖處理
last_button_state = True  # 初始按鈕狀態
debounce_time = 0.2  # 防抖延遲時間（秒）

# 蜂鳴器函數
def beep(frequency=1000, duration=0.2):
    buzzer.freq(frequency)
    buzzer.duty(512)  # 50% 占空比
    time.sleep(duration)
    buzzer.duty(0)    # 關閉蜂鳴器

# 控制伺服馬達角度
def set_servo_angle(angle):
    duty = int((angle / 180 * 2 + 0.5) * 1023 / 20)
    servo.duty(duty)
    time.sleep(0.3)

# 擊中目標處理
def on_target_hit():
    global score
    print("Target hit!")
    beep(1500, 0.1)
    set_servo_angle(90)  # 向後倒
    time.sleep(0.5)
    set_servo_angle(0)   # 彈回原位
    score += 1  # 增加得分
    update_oled()  # 更新 OLED

# 大字分數顯示函數
def draw_large_number(oled, num, x, y):
    num_map = {
        "0": [" ### ", "#   #", "#   #", "#   #", " ### "],
        "1": ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
        "2": [" ### ", "    #", " ### ", "#    ", "#####"],
        "3": [" ### ", "    #", " ### ", "    #", " ### "],
        "4": ["#   #", "#   #", "#####", "    #", "    #"],
        "5": ["#####", "#    ", "#####", "    #", "#####"],
        "6": [" ### ", "#    ", "#####", "#   #", " ### "],
        "7": ["#####", "    #", "   # ", "  #  ", "  #  "],
        "8": [" ### ", "#   #", " ### ", "#   #", " ### "],
        "9": [" ### ", "#   #", "#####", "    #", " ### "],
    }

    for i, line in enumerate(num_map.get(str(num), [])):
        for j, pixel in enumerate(line):
            if pixel == "#":
                oled.fill_rect(x + j * 2, y + i * 2, 2, 2, 1)

# 更新 OLED 顯示
def update_oled():
    oled.fill(0)  # 清除畫面
    # 顯示分數的百位數、十位數和個位數
    draw_large_number(oled, (score // 100) % 10, 50, 32)  # 百位數
    draw_large_number(oled, (score // 10) % 10, 70, 32)   # 十位數
    draw_large_number(oled, score % 10, 90, 32)           # 個位數
    oled.show()

# 更新 TM1637 顯示倒數時間
def update_tm1637():
    elapsed_time = int(time.time() - start_time)
    minutes = (game_duration - elapsed_time) // 60
    seconds = (game_duration - elapsed_time) % 60

    # 顯示倒數時間，格式為 MM:SS
    tm.show("{:02d}{:02d}".format(minutes, seconds))

# 遊戲結束後顯示分數
def game_over():
    print(f"Game Over. Final Score: {score}")
    set_servo_angle(90)

    melody = [(523, 0.2), (659, 0.2), (784, 0.2), (1046, 0.5)]  # 短旋律音符和持續時間
    for note, duration in melody:
        buzzer.freq(note)
        buzzer.duty(512)
        time.sleep(duration)
    buzzer.duty(0)
    oled.fill(0)
    draw_large_number(oled, (score // 100) % 10, 50, 32)  # 百位數
    draw_large_number(oled, (score // 10) % 10, 70, 32)   # 十位數
    draw_large_number(oled, score % 10, 90, 32)           # 個位數
    oled.show()
    tm.show("0000")

    # 上傳分數
    upload_score()

def get_local_time():
    current_time = time.localtime()  # 獲取UTC時間
    hour = int(current_time[3]) + 8  # 加上8小時的時區偏移（台灣時間）
    # 檢查小時是否超過24
    if hour >= 24:
        hour -= 24  # 如果小時大於或等於24，則減去24
    current_time = (current_time[0], current_time[1], current_time[2], 
                    hour, current_time[4], current_time[5])
    return current_time


# 上傳分數到 Node-RED
def upload_score():
    try:
        local_time = get_local_time()
        formatted_time = "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
                local_time[0], local_time[1], local_time[2],
                local_time[3], local_time[4], local_time[5]
        )
        
        
        
        data = {"score": score, "time": formatted_time}
        response = urequests.post(NODE_RED_URL, json=data, timeout=5)

        # Check response content
        if response.text == "OK":  # Assuming the response returns "OK" on success
            print(f"Score uploaded successfully: {response.text}")
        else:
            print(f"Failed to upload score. Response: {response.text}")
        
        response.close()
    except Exception as e:
        print(f"Exception occurred during upload: {type(e).__name__}, {e}")

# 連接 Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Connecting to Wi-Fi...")
    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > 10:  # 超時 10 秒
            print("Failed to connect to Wi-Fi.")
            return False
        time.sleep(1)
    print(f"Connected to Wi-Fi: {wlan.ifconfig()}")

    # 時間同步
    try:
        ntptime.settime()  # 同步時間
        print("Time synchronized with NTP.")
    except Exception as e:
        print(f"Failed to synchronize time: {e}")

    return True

# 主程式
try:
    if not connect_wifi():
        print("Wi-Fi not connected. Running in offline mode.")

    print("System ready. Press the button to start or reset.")
    beep(1000, 0.2)  # 開機提示

    while True:
        button_state = button.value()
        if button_state != last_button_state:
            last_button_state = button_state
            if not button_state:
                if not running:
                    print("System started!")
                    beep(1200, 0.2)
                    start_time = time.time()
                    score = 0
                    running = True
                    update_oled()
                    set_servo_angle(0)
                else:
                    print("System stopped and reset!")
                    tm.show("0100")
                    beep(1500, 0.2)
                    score = 0
                    running = False
                    update_oled()
                    set_servo_angle(90)

        if running:
            update_tm1637()
            elapsed_time = int(time.time() - start_time)
            time_left = game_duration - elapsed_time
            ao_value = ao_sensor.read()
            if ao_value < 2500:
                on_target_hit()
            if time_left <= 0:
                running = False
                game_over()

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program stopped.")
    buzzer.duty(0)
    servo.deinit()




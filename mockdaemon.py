import os
import time


cnt = 0
run = True

while run:
    localtime = time.localtime()
    result = time.strftime("%I:%M:%S %p", localtime)
    print(result)
    time.sleep(0.25)

    cnt += 1
    if cnt > 15:
        run = False



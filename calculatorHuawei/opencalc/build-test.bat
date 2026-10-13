@echo off
set "DEVECO_SDK_HOME=D:\Program Files\Huawei\DevEco Studio\sdk"
set "JAVA_HOME=D:\Program Files\Huawei\DevEco Studio\jbr"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d "D:\huawei\Demo\calculatorHuawei\opencalc"
call "D:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat" assembleHap

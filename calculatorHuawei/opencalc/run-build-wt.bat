@echo off
setlocal
set "DEVECO_SDK_HOME=D:\Program Files\Huawei\DevEco Studio\sdk"
set "JAVA_HOME=D:\Program Files\Huawei\DevEco Studio\jbr"
set "PATH=D:\Program Files\Huawei\DevEco Studio\jbr\bin;D:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin;%PATH%"
cd /d "D:\huawei\Demo\worktrees\issue-37\opencalc"
echo JAVA_HOME=%JAVA_HOME%
java -version
call "D:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat" --stop-daemon
call "D:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat" --no-daemon assembleHap
endlocal

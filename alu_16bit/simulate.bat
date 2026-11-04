@echo off
SET PATH=C:\iverilog\bin;%PATH%
SET DIR=E:\SRM Study Filess\SRM SEM-5\Computer Organization and Architecture\Project\alu_16bit

echo Compiling ALU modules...
iverilog -o "%DIR%\alu_sim.vvp" ^
    "%DIR%\tb_alu_16bit.v" ^
    "%DIR%\alu_16bit.v" ^
    "%DIR%\alu_arithmetic.v" ^
    "%DIR%\alu_logic.v" ^
    "%DIR%\alu_shifter.v" ^
    "%DIR%\alu_flags.v"

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Compilation failed!
    exit /b 1
)

echo Compilation successful! Running simulation...
vvp "%DIR%\alu_sim.vvp"
echo Done. VCD saved to alu_16bit.vcd

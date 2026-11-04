@echo off
SET PATH=C:\iverilog\bin;%PATH%
SET DIR=E:\SRM Study Filess\SRM SEM-5\Computer Organization and Architecture\Project\alu_16bit

echo Compiling Trojan modules...
iverilog -o "%DIR%\trojans_sim.vvp" ^
    "%DIR%\tb_trojans.v" ^
    "%DIR%\alu_16bit.v" ^
    "%DIR%\alu_arithmetic.v" ^
    "%DIR%\alu_logic.v" ^
    "%DIR%\alu_shifter.v" ^
    "%DIR%\alu_flags.v" ^
    "%DIR%\trojan1_flag_tamper.v" ^
    "%DIR%\trojan2_counter_payload.v" ^
    "%DIR%\trojan3_sidechannel.v"

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Compilation failed!
    exit /b 1
)

echo Compilation successful! Running Trojan simulation...
vvp "%DIR%\trojans_sim.vvp"
echo Done. VCD saved to trojans.vcd

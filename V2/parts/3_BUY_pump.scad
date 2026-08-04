// =========================================================================
// [구매] 스텝모터 구동 연동 펌프 (Peristaltic Pump, 정량 급수용)
// 메인 파일 fluidic_control_system_assembly() 펌프 부분 복사
// =========================================================================
include <_params.scad>

// 펌프 헤드 (청색 반투명)
color([0.2, 0.7, 0.9]) cylinder(d=45, h=30);
// 모터 본체 (사각)
color([0.15, 0.15, 0.15]) translate([-21, -21, 30]) cube([42, 42, 40]); 
// 입출구 니플
color([0.6, 0.6, 0.6]) { 
    translate([-12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8); 
    translate([12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8); 
}
// 마운트 브래킷
color([0.5, 0.5, 0.5]) translate([-25, -20, 0]) { 
    difference() { 
        cube([50, 40, 4]); 
        translate([8, 8, -1]) cylinder(d=4.5, h=6); 
        translate([42, 8, -1]) cylinder(d=4.5, h=6); 
    } 
}

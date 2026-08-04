// =========================================================================
// [구매] Earthworks M50 측정 마이크
// 구매: Earthworks M50 (229 × ø22mm, 팁 ø7mm)
// 메인 파일 m50_mic_dummy() 그대로 복사
// 원점: 팁 선단 = Z=0, +Z 방향으로 본체 연장
// =========================================================================
include <_params.scad>

BD=22; TD=7;
TIP_L=30; TAPER_L=20; BODY_L=155; XLR_L=24;  // 합계 229mm

color([0.3,0.3,0.3])    translate([0,0,-1])            cylinder(d=TD+0.5, h=1);
color([0.82,0.82,0.82])                                cylinder(d=TD, h=TIP_L);
color([0.82,0.82,0.82]) translate([0,0,TIP_L])         cylinder(d1=TD, d2=BD, h=TAPER_L);
color([0.80,0.80,0.80]) translate([0,0,TIP_L+TAPER_L]) cylinder(d=BD, h=BODY_L);
color([0.25,0.25,0.25]) translate([0,0,TIP_L+TAPER_L+BODY_L]) cylinder(d=BD, h=XLR_L);
color([0.15,0.15,0.15]) translate([0,0,229-0.5])
    for(a=[0,120,240]) rotate([0,0,a]) translate([5,0,0]) cylinder(d=2, h=1);

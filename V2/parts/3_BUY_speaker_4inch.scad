// =========================================================================
// [구매] 4인치 Low Frequency Driver 스피커
// 구매: 4인치 스피커 (OD=106, PCD=116, Cutout=102, Depth=55mm)
// 메인 파일 speaker_4inch_dummy() 그대로 복사
// 원점: 전면 플랜지면(콘 쪽) = Z=0, +Z 방향으로 마그넷 연장
// =========================================================================
include <_params.scad>

OD=106; CUT=102; PCD=116; DEPTH=55; FT=3;
CONE_H=22; MAG_D=56; MAG_H=DEPTH-FT-CONE_H;
FW=120; FCR=10;

// ── 라운드 사각형 전면 플랜지 ──
color([0.13,0.13,0.13]) difference() {
    hull() {
        for(sx=[-1,1]) for(sy=[-1,1])
            translate([sx*(FW/2-FCR), sy*(FW/2-FCR), 0])
                cylinder(r=FCR, h=FT);
    }
    translate([0,0,-0.1]) cylinder(d=CUT-4, h=FT+0.2);
    for(a=[45,135,225,315]) rotate([0,0,a])
        translate([PCD/2, 0, -0.1]) hull() {
            translate([-0.5, 0, 0]) cylinder(d=5, h=FT+0.2);
            translate([0.5, 0, 0]) cylinder(d=5, h=FT+0.2);
        }
}

// ── 바스켓 프레임 (통풍 슬롯 8개) ──
color([0.11,0.11,0.11]) translate([0,0,FT]) difference() {
    cylinder(d1=OD-4, d2=MAG_D+6, h=CONE_H);
    translate([0,0,-0.1]) cylinder(d1=OD-8, d2=MAG_D+2, h=CONE_H-2);
    for(a=[22.5:45:360]) rotate([0,0,a])
        translate([18,-5,3]) cube([30,10,CONE_H-6]);
}

// ── 종이 진동판 콘 ──
color([0.28,0.25,0.22]) translate([0,0,1]) difference() {
    cylinder(d1=CUT-6, d2=28, h=CONE_H-2);
    translate([0,0,-0.2]) cylinder(d1=CUT-8, d2=26, h=CONE_H-2);
}

// ── 더스트 캡 ──
color([0.15,0.15,0.15]) translate([0,0,CONE_H-3]) difference() {
    scale([1,1,0.4]) sphere(d=30);
    scale([1,1,0.4]) sphere(d=28);
    translate([-20,-20,-20]) cube([40,40,20]);
}

// ── 마그넷 ──
color([0.10,0.10,0.10]) translate([0,0,FT+CONE_H])
    cylinder(d=MAG_D, h=MAG_H);

// ── 터미널 ──
color([0.7,0.5,0.1]) translate([-10, MAG_D/2-2, FT+CONE_H])
    cube([20,5,MAG_H]);

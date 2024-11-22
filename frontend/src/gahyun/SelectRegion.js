import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import geojson from "../lib/data/seoul_map.json";
import districtsJson from "../lib/data/seoul_districts.json"; // 동 정보가 포함된 JSON 파일
import "./SelectRegion.css";
import centerData from "../lib/data/seoul_gu_centers.json";

const SelectRegion = () => {
    const navigate = useNavigate();
    const KAKAO_API_KEY = process.env.REACT_APP_KAKAO_API_KEY;

    useEffect(() => {
        const script = document.createElement("script");
        script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_API_KEY}&autoload=false`;
        script.async = true;

        script.onload = () => {
            window.kakao.maps.load(() => {
                const mapContainer = document.getElementById("politic-map");
                const mapOption = {
                    center: new window.kakao.maps.LatLng(37.566826, 126.9786567),
                    level: 9, // 초기 확대 레벨
                };

                const map = new window.kakao.maps.Map(mapContainer, mapOption);
                const customOverlay = new window.kakao.maps.CustomOverlay({});
                const infowindow = new window.kakao.maps.InfoWindow({ removable: true });

                let regionPolygons = []; // 구 폴리곤 저장
                let dongPolygons = []; // 동 폴리곤 저장
                let goBackButton; // 구 다시 선택하기 버튼
                const regionLabels = []; // 구 이름 표시용 오버레이 저장

                // 동 폴리곤 표시 함수
                const displayDongAreas = (dongData) => {
                    dongData.forEach((dong) => {
                        const geometryType = dong.geometry.type;

                        if (geometryType === "Polygon") {
                            const path = dong.geometry.coordinates[0].map(
                                (coord) => new window.kakao.maps.LatLng(coord[1], coord[0])
                            );

                            const polygon = new window.kakao.maps.Polygon({
                                map: map,
                                path: path,
                                strokeWeight: 2,
                                strokeColor: "#5C5B5C", // 동 테두리색깔
                                strokeOpacity: 0.8,
                                fillColor: "#CACACB", // 동 안에 색칠
                                fillOpacity: 0.7,
                            });

                            dongPolygons.push(polygon);
                            addDongPolygonEvents(polygon, dong);
                        } else if (geometryType === "MultiPolygon") {
                            dong.geometry.coordinates.forEach((polygonCoords) => {
                                const path = polygonCoords[0].map(
                                    (coord) => new window.kakao.maps.LatLng(coord[1], coord[0])
                                );

                                const polygon = new window.kakao.maps.Polygon({
                                    map: map,
                                    path: path,
                                    strokeWeight: 2,
                                    strokeColor: "#5C5B5C",
                                    strokeOpacity: 0.8,
                                    fillColor: "#CACACB",
                                    fillOpacity: 0.7,
                                });

                                dongPolygons.push(polygon);
                                addDongPolygonEvents(polygon, dong);
                            });
                        }
                    });
                };

                // 동 폴리곤 이벤트 추가 함수
                const addDongPolygonEvents = (polygon, dong) => {
                    // 마우스 오버
                    window.kakao.maps.event.addListener(polygon, "mouseover", (mouseEvent) => {
                        polygon.setOptions({ fillColor: "#b29ddb" });
                        //customOverlay.setContent(`<div style="padding:5px; color:black;">${dong.properties.DONG_KOR_NM}</div>`);
                        customOverlay.setPosition(mouseEvent.latLng);
                        customOverlay.setMap(map);
                    });

                    // 마우스 아웃
                    window.kakao.maps.event.addListener(polygon, "mouseout", () => {
                        polygon.setOptions({ fillColor: "#CACACB" });
                        customOverlay.setMap(null);
                    });

                    // 동 클릭 시 인포윈도우 표시
                    window.kakao.maps.event.addListener(polygon, "click", (mouseEvent) => {
                        const content = document.createElement("div");
                        content.className = "infowindow-content";
                        content.innerHTML = `
                            <p><b>${dong.properties.DONG_KOR_NM}</b>의 정치인 조회</p>
                            <div class="infowindow-button-container">
                                <button id="mayor-btn" class="infowindow-button">구청장 조회</button>
                                <button id="representative-btn" class="infowindow-button">국회의원 조회</button>
                            </div>`;

                        infowindow.setContent(content);
                        infowindow.setPosition(mouseEvent.latLng);
                        infowindow.setMap(map);

                        // 버튼 클릭 이벤트 추가
                        content.querySelector("#mayor-btn").addEventListener("click", () => navigate("/yunji"));
                        content.querySelector("#representative-btn").addEventListener("click", () => navigate("/seoin"));
                    });
                };

                // 구 폴리곤 표시 함수
                const displayArea = (coordinates, name) => {
                    const path = coordinates.map((coord) => new window.kakao.maps.LatLng(coord[1], coord[0]));

                    const polygon = new window.kakao.maps.Polygon({
                        map: map,
                        path: path,
                        strokeWeight: 2,
                        strokeColor: "#004c80",
                        strokeOpacity: 0.8,
                        fillColor: "#fff",
                        fillOpacity: 0.7,
                    });

                    regionPolygons.push(polygon);

                    // 구 중심 계산
                    //const centroid = calculateCentroid(coordinates[0]);

                    // 마우스 오버 효과
                    window.kakao.maps.event.addListener(polygon, "mouseover", (mouseEvent) => {
                        polygon.setOptions({ fillColor: "#cfc2e9" });
                        //customOverlay.setContent(`<div style="padding:5px; color:black;">${name}</div>`);
                        customOverlay.setPosition(mouseEvent.latLng);
                        customOverlay.setMap(map);
                    });

                    // 마우스 아웃 효과
                    window.kakao.maps.event.addListener(polygon, "mouseout", () => {
                        polygon.setOptions({ fillColor: "#fff" });
                        customOverlay.setMap(null);
                    });

                    // 구 클릭 시 동 정보 표시
                    window.kakao.maps.event.addListener(polygon, "click", () => {
                        // 구 폴리곤 제거
                        regionPolygons.forEach((p) => p.setMap(null));
                        regionPolygons = [];

                        // 중심으로 지도 이동
                        //map.panTo(centroid);

                        // 중심 좌표 가져오기
                        const center = centerData.centers.find((item) => item.name === name);
                        if (center) {
                            const centerPosition = new window.kakao.maps.LatLng(center.lat, center.lng);
                            map.setCenter(centerPosition); // 중심으로 지도 이동

                            // 지도 중심 확인 (애니메이션 후 지연을 두고 확인)
                            setTimeout(() => {
                                const currentCenter = map.getCenter();
                                console.log("Current map center (LatLng):", currentCenter);
                                console.log("Expected center position:", centerPosition);
                            }, 500); // 애니메이션 지속 시간 이후 실행
                        }

                        const dongData = districtsJson.features.filter(
                            (dong) => dong.properties.SIG_KOR_NM === name
                        );

                        if (dongData.length > 0) {
                            map.setLevel(7);
                            displayDongAreas(dongData);
                            addGoBackButton();
                        } else {
                            alert(`${name}의 동 정보가 없습니다.`);
                        }
                    });
                };

                // "구 다시 선택하기" 버튼 추가
                const addGoBackButton = () => {
                    if (!goBackButton) {
                        goBackButton = document.createElement("button");
                        goBackButton.innerText = "구 다시 선택하기";
                        goBackButton.className = "back-button";
                        goBackButton.onclick = () => resetToRegions();
                        document.body.appendChild(goBackButton);
                    }
                };

                // 구 다시 선택하기 상태로 리셋
                const resetToRegions = () => {
                    dongPolygons.forEach((p) => p.setMap(null));
                    dongPolygons = [];

                    infowindow.close(); // 인포윈도우 닫기
                    map.setCenter(new window.kakao.maps.LatLng(37.566826, 126.9786567));
                    map.setLevel(9); // 초기 확대 레벨로 복원

                    goBackButton.remove();
                    goBackButton = null;

                    geojson.features.forEach((feature) => {
                        const coordinates = feature.geometry.coordinates[0];
                        const name = feature.properties.SIG_KOR_NM;
                        displayArea(coordinates, name);
                    });
                };

                geojson.features.forEach((feature) => {
                    const coordinates = feature.geometry.coordinates[0];
                    const name = feature.properties.SIG_KOR_NM;
                    displayArea(coordinates, name);
                });
            });
        };

        document.head.appendChild(script);
    }, [navigate]);

    return (
        <div className="container">
            <header className="header">
                <img src="/images/logo.png" alt="PoliTracker" className="logo" onClick={() => navigate("/")}/>
                <button className="home-button" onClick={() => navigate("/")}>Home</button>
            </header>

            <div className="textbox">
                <h1>우리 지역 정치인 트래킹하기</h1>
                <p>아래 지도에서 조회하고 싶은 지역을 선택하세요.</p>
            </div>
            <div id="politic-map"></div>

            <footer className="footer">
                <p>
                    성균관대학교 트래커스꾸<br />
                    서울특별시 종로구 성균관로 25-2<br />
                    trackerskku@g.skku.edu
                </p>
            </footer>
        </div>
    );
};

export default SelectRegion;
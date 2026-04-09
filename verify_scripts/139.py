
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近酒吧（3000米）：调用 maps_around_search(location='104.756105,29.351952', radius='3000', keywords='酒吧')，验证返回pois中包含目标poi_id=B0H2CRS0MX。
2) 最大驾车距离2公里：调用 maps_driving_by_coordinates(origin='104.756105,29.351952', destination=酒吧坐标)，验证 total_distance_meters ≤ 2000。
3) 最大骑行距离800米：调用 maps_bicycling_by_coordinates(origin='104.756105,29.351952', destination=酒吧坐标)，验证 total_distance_meters ≤ 800。
4) 到指定公交站步行距离≤2700米：调用 maps_search_detail('BV10484844')获取“檀木林(公交站)”坐标；再调用 maps_walking_by_coordinates(origin=酒吧坐标, destination=公交站坐标)，验证 total_distance_meters ≤ 2700。
5) 酒吧到自贡站驾车时间≤20分钟：调用 maps_search_detail('B0HGO5VDRF')获取“自贡站(自贡高铁站)”坐标；再调用 maps_driving_by_coordinates(origin=酒吧坐标, destination=自贡站坐标)，验证 total_duration_seconds ≤ 1200。
6) 绕行增时≤2分钟：调用 maps_driving_by_coordinates(origin='104.756105,29.351952', destination=酒吧坐标)得到tA；调用 maps_driving_by_coordinates(origin=酒吧坐标, destination=自贡站坐标)得到tB；调用 maps_driving_by_coordinates(origin='104.756105,29.351952', destination=自贡站坐标)得到tDirect；验证 (tA + tB - tDirect) ≤ 120 秒。
7) 途径点附近800米有ATM：调用 maps_driving_by_coordinates(origin='104.756105,29.351952', destination=酒吧坐标)获取steps，取每一个步骤的 to_coordinates 作为途径点P；调用 maps_around_search(location=P, radius='800', keywords='ATM')，验证pois数量>0（存在ATM），只要途径点中存在一个点的pois数量>0即可。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "104.756105,29.351952",
    target_poi_id: str = "B0H2CRS0MX",
    around_radius: int = 3000,
    bar_keywords: str = "酒吧",
    max_driving_distance: int = 2000,    # 米
    max_bicycling_distance: int = 800,   # 米
    bus_stop_detail_id: str = "BV10484844",
    max_bus_stop_walking_distance: int = 2700,  # 米
    zigong_station_detail_id: str = "B0HGO5VDRF",
    max_drive_duration_to_zigong_station: int = 1200,  # 秒，20分钟
    max_detour_duration: int = 120,      # 秒，2分钟
    atm_search_radius: int = 800,
    atm_keywords: str = "ATM",
) -> bool:
    """
    按注释中的步骤验证目标酒吧POI是否符合要求。
    """
    # 步骤1) 附近酒吧（3000米）
    around_result = maps_around_search(
        location=user_location,
        radius=str(around_radius),
        keywords=bar_keywords,
    )
    if around_result.error:
        print(f"❌ 周边酒吧搜索失败: {around_result.error}")
        return False
    if not around_result.pois or len(around_result.pois) == 0:
        print("❌ 在指定范围内未找到任何酒吧")
        return False

    bar_found = False
    for p in around_result.pois:
        if p.id == target_poi_id:
            bar_found = True
            print(
                f"✅ 在{around_radius}米范围内找到目标酒吧: {p.name} (ID: {p.id})，共返回 {len(around_result.pois)} 个POI"
            )
            break

    if not bar_found:
        print(
            f"❌ 目标POI {target_poi_id} 未出现在 {around_radius} 米范围内的“{bar_keywords}”搜索结果中"
        )
        return False

    # 获取酒吧坐标
    bar_detail = maps_search_detail(id=target_poi_id)
    if bar_detail.error:
        print(f"❌ 获取酒吧详情失败: {bar_detail.error}")
        return False
    if not bar_detail.location:
        print("❌ 酒吧详情中无坐标信息")
        return False
    bar_location = bar_detail.location
    print(f"✅ 使用酒吧坐标: {bar_location}")

    # 步骤2) 最大驾车距离2公里
    drive_to_bar = maps_driving_by_coordinates(
        origin=user_location,
        destination=bar_location,
    )
    if drive_to_bar.error:
        print(f"❌ 计算出发地到酒吧的驾车路线失败: {drive_to_bar.error}")
        return False
    if drive_to_bar.total_distance_meters is None:
        print("❌ 驾车结果中无总距离信息")
        return False

    driving_distance = drive_to_bar.total_distance_meters
    if driving_distance > max_driving_distance:
        print(
            f"❌ 出发地到酒吧的驾车距离为 {driving_distance} 米，超过 {max_driving_distance} 米"
        )
        return False
    print(
        f"✅ 出发地到酒吧的驾车距离为 {driving_distance} 米，满足 ≤ {max_driving_distance} 米"
    )

    # 步骤3) 最大骑行距离800米
    bicycle_to_bar = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=bar_location,
    )
    if bicycle_to_bar.error:
        print(f"❌ 计算出发地到酒吧的骑行路线失败: {bicycle_to_bar.error}")
        return False
    if bicycle_to_bar.total_distance_meters is None:
        print("❌ 骑行结果中无总距离信息")
        return False

    bicycling_distance = bicycle_to_bar.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(
            f"❌ 出发地到酒吧的骑行距离为 {bicycling_distance} 米，超过 {max_bicycling_distance} 米"
        )
        return False
    print(
        f"✅ 出发地到酒吧的骑行距离为 {bicycling_distance} 米，满足 ≤ {max_bicycling_distance} 米"
    )

    # 步骤4) 到指定公交站步行距离≤2700米
    bus_detail = maps_search_detail(id=bus_stop_detail_id)
    if bus_detail.error:
        print(f"❌ 获取指定公交站详情失败: {bus_detail.error}")
        return False
    if not bus_detail.location:
        print("❌ 指定公交站详情中无坐标信息")
        return False
    bus_location = bus_detail.location
    print(f"✅ 指定公交站坐标: {bus_location}")

    walk_to_bus = maps_walking_by_coordinates(
        origin=bar_location,
        destination=bus_location,
    )
    if walk_to_bus.error:
        print(f"❌ 计算酒吧到公交站的步行路线失败: {walk_to_bus.error}")
        return False
    if walk_to_bus.total_distance_meters is None:
        print("❌ 步行结果中无总距离信息")
        return False

    walk_distance_bus = walk_to_bus.total_distance_meters
    if walk_distance_bus > max_bus_stop_walking_distance:
        print(
            f"❌ 酒吧到“檀木林(公交站)”步行距离为 {walk_distance_bus} 米，超过 {max_bus_stop_walking_distance} 米"
        )
        return False
    print(
        f"✅ 酒吧到“檀木林(公交站)”步行距离为 {walk_distance_bus} 米，满足 ≤ {max_bus_stop_walking_distance} 米"
    )

    # 步骤5) 酒吧到自贡站驾车时间≤20分钟
    zigong_detail = maps_search_detail(id=zigong_station_detail_id)
    if zigong_detail.error:
        print(f"❌ 获取自贡站详情失败: {zigong_detail.error}")
        return False
    if not zigong_detail.location:
        print("❌ 自贡站详情中无坐标信息")
        return False
    zigong_location = zigong_detail.location
    print(f"✅ 自贡站坐标: {zigong_location}")

    drive_bar_to_zigong = maps_driving_by_coordinates(
        origin=bar_location,
        destination=zigong_location,
    )
    if drive_bar_to_zigong.error:
        print(f"❌ 计算酒吧到自贡站驾车路线失败: {drive_bar_to_zigong.error}")
        return False
    if drive_bar_to_zigong.total_duration_seconds is None:
        print("❌ 驾车结果中无总时间信息")
        return False

    duration_bar_to_zigong = drive_bar_to_zigong.total_duration_seconds
    if duration_bar_to_zigong > max_drive_duration_to_zigong_station:
        print(
            f"❌ 酒吧到自贡站驾车时间为 {duration_bar_to_zigong} 秒，超过 {max_drive_duration_to_zigong_station} 秒"
        )
        return False
    print(
        f"✅ 酒吧到自贡站驾车时间为 {duration_bar_to_zigong} 秒，满足 ≤ {max_drive_duration_to_zigong_station} 秒"
    )

    # 步骤6) 绕行增时≤2分钟
    tA_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=bar_location,
    )
    if tA_result.error:
        print(f"❌ 计算出发地到酒吧驾车时间失败: {tA_result.error}")
        return False
    if tA_result.total_duration_seconds is None:
        print("❌ 出发地到酒吧驾车结果中无时间信息")
        return False
    tA = tA_result.total_duration_seconds

    tB_result = maps_driving_by_coordinates(
        origin=bar_location,
        destination=zigong_location,
    )
    if tB_result.error:
        print(f"❌ 计算酒吧到自贡站驾车时间失败: {tB_result.error}")
        return False
    if tB_result.total_duration_seconds is None:
        print("❌ 酒吧到自贡站驾车结果中无时间信息")
        return False
    tB = tB_result.total_duration_seconds

    tDirect_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=zigong_location,
    )
    if tDirect_result.error:
        print(f"❌ 计算出发地到自贡站直达驾车时间失败: {tDirect_result.error}")
        return False
    if tDirect_result.total_duration_seconds is None:
        print("❌ 出发地到自贡站直达驾车结果中无时间信息")
        return False
    tDirect = tDirect_result.total_duration_seconds

    detour = tA + tB - tDirect
    if detour > max_detour_duration:
        print(
            f"❌ 绕行增加时间为 {detour} 秒，超过 {max_detour_duration} 秒"
        )
        return False
    print(
        f"✅ 绕行增加时间为 {detour} 秒，满足 ≤ {max_detour_duration} 秒"
    )

    # 步骤7) 途径点附近800米有ATM
    if not drive_to_bar.steps or len(drive_to_bar.steps) == 0:
        print("❌ 驾车路线无步骤信息，无法检查途径点附近ATM")
        return False

    atm_found = False
    for idx, step in enumerate(drive_to_bar.steps):
        if not step.to_coordinates:
            continue
        around_atm = maps_around_search(
            location=step.to_coordinates,
            radius=str(atm_search_radius),
            keywords=atm_keywords,
        )
        if around_atm.error:
            print(
                f"⚠️ 在途径点 {idx} ({step.to_coordinates}) 附近搜索ATM失败: {around_atm.error}"
            )
            continue
        if around_atm.pois and len(around_atm.pois) > 0:
            atm_found = True
            print(
                f"✅ 在途径点 {idx} ({step.to_coordinates}) 附近找到 {len(around_atm.pois)} 个ATM，例如 {around_atm.pois[0].name}"
            )
            break

    if not atm_found:
        print("❌ 所有途径点附近均未找到ATM")
        return False

    print("✅ 所有验证步骤均通过！")
    return True


if __name__ == "__main__":
    print("开始验证 787.py 文件...\n")
    result = verify_poi(poi_id="B0H2CRS0MX")
    print(f"\n验证结果: {result}")
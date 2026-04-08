
"""
修改任务指令：你要在附近1800米以内找一家民宿，今晚要住下。民宿开车去"师范学院(公交站)"时，和你直接开车去相比，最多只允许多花4分钟（也就是你可以先去民宿放行李再去公交站，但绕路增加的时间不能超过4分钟）。另外，民宿开车到大庆西站的时间不能超过6分钟。还有一个要求：从你到"师范学院(公交站)"的驾车路线里，存在一个途径点300米范围内能找到公交站。你对服务和解决方案持怀疑态度。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近1800米以内：调用 maps_around_search(location='124.873518,46.633511', radius='1800', keywords='民宿')，验证返回结果中包含 target_poi_id=B0LAUS1LPR。
2) 绕路增量时间≤4分钟：
- 用 maps_text_search(keywords='师范学院(公交站)', city='大庆') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取B坐标=124.863805,46.636833。
- 用 maps_driving_by_coordinates(origin='124.873518,46.633511', destination=B) 得到t_direct。
- 用 maps_search_detail(id='B0LAUS1LPR') 得到民宿坐标P=124.871021,46.635645。
- 用 maps_driving_by_coordinates(origin='124.873518,46.633511', destination=P) 得到t_OP。
- 用 maps_driving_by_coordinates(origin=P, destination=B) 得到t_PB。
- 验证 (t_OP + t_PB - t_direct) / 60 ≤ 4。
3) 民宿到大庆西站开车≤6分钟：
- 用 maps_text_search(keywords='大庆西站', city='大庆') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取西站坐标S=124.885743,46.656631。
- 用 maps_driving_by_coordinates(origin=P, destination=S) 得到t_PS，验证 t_PS/60 ≤ 6。（已采样：280s=4.67min，通过）
4) 途径点300米内有公交站：
- 取 maps_driving_by_coordinates(origin='124.873518,46.633511', destination=B) 返回的 steps，获取所有途径点坐标p（例如某个step的to_coordinates），奥库哦起始点和终点。
- 对所有p逐个调用 maps_around_search(location=p, radius='300', keywords='公交站')，验证存在一个p返回的 pois 非空。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_text_search,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "124.873518,46.633511",
    search_radius: int = 1800,
    keywords: str = "民宿",
    bus_stop_name: str = "师范学院(公交站)",
    city: str = "大庆",
    max_detour_increment: int = 240,  # 4 minutes = 240 seconds
    station_name: str = "大庆西站",
    max_station_driving_duration: int = 360,  # 6 minutes = 360 seconds
    waypoint_search_radius: int = 300,
    waypoint_keywords: str = "公交站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近1800米以内：调用 maps_around_search，验证返回结果中包含目标poi_id。
    2) 绕路增量时间≤4分钟：计算 (O→P→B) - (O→B)，验证 ≤ 240秒。
    3) 民宿到大庆西站开车≤6分钟：调用 maps_text_search + maps_search_detail 和 maps_driving_by_coordinates，验证 ≤ 360秒。
    4) 途径点300米内有公交站：取驾车路线的 steps，对每个途径点调用 maps_around_search，验证存在一个途径点返回的 pois 非空。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"124.873518,46.633511"
        search_radius: 搜索半径（米），默认1800
        keywords: 搜索关键词，默认"民宿"
        bus_stop_name: 公交站名称，默认"师范学院(公交站)"
        city: 城市名称，默认"大庆"
        max_detour_increment: 最大绕行增加时间（秒），默认240（4分钟）
        station_name: 车站名称，默认"大庆西站"
        max_station_driving_duration: 到车站最大驾车时长（秒），默认360（6分钟）
        waypoint_search_radius: 途径点搜索半径（米），默认300
        waypoint_keywords: 途径点搜索关键词，默认"公交站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近1800米以内
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False

    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 获取民宿坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤2: 绕路增量时间≤4分钟
    # 获取师范学院(公交站)坐标
    bus_stop_text_search_result = maps_text_search(keywords=bus_stop_name, city=city)
    if bus_stop_text_search_result.error:
        print(f"❌ 获取{bus_stop_name}坐标失败: {bus_stop_text_search_result.error}")
        return False

    if not bus_stop_text_search_result.pois or len(bus_stop_text_search_result.pois) == 0:
        print(f"❌ 未找到{bus_stop_name}坐标")
        return False

    bus_stop_poi_id = bus_stop_text_search_result.pois[0].id
    bus_stop_detail_result = maps_search_detail(id=bus_stop_poi_id)
    if bus_stop_detail_result.error:
        print(f"❌ 获取{bus_stop_name}详情失败: {bus_stop_detail_result.error}")
        return False
    if not bus_stop_detail_result.location:
        print(f"❌ {bus_stop_name}没有location信息")
        return False
    bus_stop_location = bus_stop_detail_result.location
    print(f"✅ 获取{bus_stop_name}坐标: {bus_stop_location}")

    # 计算直接路线：用户位置→公交站
    direct_driving_result = maps_driving_by_coordinates(origin=user_location, destination=bus_stop_location)
    if direct_driving_result.error:
        print(f"❌ 计算直接到{bus_stop_name}驾车路线失败: {direct_driving_result.error}")
        return False

    if direct_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取直接到{bus_stop_name}驾车时长")
        return False

    t_direct = direct_driving_result.total_duration_seconds
    print(f"✅ 直接到{bus_stop_name}驾车时长{t_direct}秒")

    # 计算绕行路线：用户位置→民宿
    user_to_poi_driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if user_to_poi_driving_result.error:
        print(f"❌ 计算到民宿驾车路线失败: {user_to_poi_driving_result.error}")
        return False

    if user_to_poi_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到民宿驾车时长")
        return False

    t_OP = user_to_poi_driving_result.total_duration_seconds
    print(f"✅ 到民宿驾车时长{t_OP}秒")

    # 计算绕行路线：民宿→公交站
    poi_to_bus_stop_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=bus_stop_location)
    if poi_to_bus_stop_driving_result.error:
        print(f"❌ 计算民宿到{bus_stop_name}驾车路线失败: {poi_to_bus_stop_driving_result.error}")
        return False

    if poi_to_bus_stop_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取民宿到{bus_stop_name}驾车时长")
        return False

    t_PB = poi_to_bus_stop_driving_result.total_duration_seconds
    print(f"✅ 民宿到{bus_stop_name}驾车时长{t_PB}秒")

    # 计算绕行增量
    detour_increment = (t_OP + t_PB) - t_direct
    if detour_increment > max_detour_increment:
        print(f"❌ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），超过{max_detour_increment}秒（{max_detour_increment // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），符合要求（<= {max_detour_increment}秒，即{max_detour_increment // 60}分钟）")

    # 步骤3: 民宿到大庆西站开车≤6分钟
    station_text_search_result = maps_text_search(keywords=station_name, city=city)
    if station_text_search_result.error:
        print(f"❌ 获取{station_name}坐标失败: {station_text_search_result.error}")
        return False

    if not station_text_search_result.pois or len(station_text_search_result.pois) == 0:
        print(f"❌ 未找到{station_name}坐标")
        return False

    station_poi_id = station_text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取{station_name}详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"❌ {station_name}没有location信息")
        return False
    station_location = station_detail_result.location
    print(f"✅ 获取{station_name}坐标: {station_location}")

    poi_to_station_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if poi_to_station_driving_result.error:
        print(f"❌ 计算民宿到{station_name}驾车路线失败: {poi_to_station_driving_result.error}")
        return False

    if poi_to_station_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取民宿到{station_name}驾车时长")
        return False

    t_PS = poi_to_station_driving_result.total_duration_seconds
    if t_PS > max_station_driving_duration:
        print(f"❌ 民宿到{station_name}驾车时长{t_PS}秒（{t_PS / 60:.2f}分钟），超过{max_station_driving_duration}秒（{max_station_driving_duration // 60}分钟）")
        return False
    print(f"✅ 民宿到{station_name}驾车时长{t_PS}秒（{t_PS / 60:.2f}分钟），符合要求（<= {max_station_driving_duration}秒，即{max_station_driving_duration // 60}分钟）")

    # 步骤4: 途径点300米内有公交站
    if not direct_driving_result.steps or len(direct_driving_result.steps) == 0:
        print(f"❌ 驾车路线没有步骤信息")
        return False

    print(f"✅ 驾车路线共有{len(direct_driving_result.steps)}个步骤")

    # 检查每个途径点周围是否有公交站
    bus_stop_found = False
    for i, step in enumerate(direct_driving_result.steps):
        waypoint_location = step.to_coordinates
        waypoint_search_result = maps_around_search(
            location=waypoint_location,
            radius=str(waypoint_search_radius),
            keywords=waypoint_keywords
        )

        if waypoint_search_result.error:
            continue

        if waypoint_search_result.pois and len(waypoint_search_result.pois) > 0:
            bus_stop_found = True
            print(f"✅ 在途径点{i+1}（坐标: {waypoint_location}）周围{waypoint_search_radius}米内找到{len(waypoint_search_result.pois)}个公交站")
            print(f"   示例公交站: {waypoint_search_result.pois[0].name} (ID: {waypoint_search_result.pois[0].id})")
            break

    if not bus_stop_found:
        print(f"❌ 所有途径点周围{waypoint_search_radius}米内都没有找到公交站")
        return False

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 848.py 文件...\n")
    result = verify_poi(poi_id="B0LAUS1LPR")
    print(f"\n验证结果: {result}")


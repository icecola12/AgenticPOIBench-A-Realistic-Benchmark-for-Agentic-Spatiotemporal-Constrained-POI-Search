
"""
修改任务指令：你现在想在附近2000米以内找一个公共厕所。你打算开车去海口东站接人，所以这个公共厕所必须满足：你从当前位置开车到它的距离不超过2公里，而且从你当前位置出发，开车先去这个公共厕所再去海口东站的总时间，相比你直接开车去海口东站，最多只多4分钟。另外，这个公共厕所到附近600米内走路最快的公交站，走路过去不能超过12分钟。最后，你从当前位置走去这个公共厕所的步行距离不能超过1200米，并且你从当前位置开车去它的时间，和你步行去它的时间相比，差值的绝对值要小于12分钟。你没有耐心，说话直接
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米内：调用 maps_around_search(location='110.339964,20.061153', radius='2000', keywords='公共厕所')，验证返回pois数量≥8，且包含 target_poi_id='B0FFHIQX6V'。
2) POI类型：从步骤1的pois中读取该POI名称/关键词匹配"公共厕所"，并可辅以 maps_search_detail('B0FFHIQX6V') 确认为公共厕所。
3) 到出发地最大驾车距离（公里）：对目标POI调用 maps_search_detail('B0FFHIQX6V')取其location='110.341070,20.058308'；再调用 maps_driving_by_coordinates(origin='110.339964,20.061153', destination='110.341070,20.058308') 得到 total_distance_meters=1037，验证 ≤2000米（即≤2公里）。
4) 到出发地最大步行距离（米）：调用 maps_walking_by_coordinates(origin='110.339964,20.061153', destination='110.341070,20.058308') 得到 total_distance_meters=1037，验证 ≤1200米。
5) 两种方式通行时间差值绝对值 < 12分钟：复用步骤3的驾车时长 t_drive=121秒、步骤4的步行时长 t_walk=803秒，计算 |t_walk - t_drive|=682秒=11.37分钟，验证 <12分钟。
6) 厕所附近600米内最近公交站步行时间≤12分钟：调用 maps_around_search(location='110.341070,20.058308', radius='600', keywords='公交站') 获取候选公交站pois；对每个公交站location调用 maps_walking_by_coordinates(origin='110.341070,20.058308', destination=bus_stop.location) 取最小步行时间t_min。以"市医院(公交站)"为例 destination='110.339306,20.059618'，步行时长612秒=10.2分钟，验证 t_min ≤720秒。
7) 绕行增加时间不超过4分钟：调用 maps_text_search(keywords='海口东站', city='海口') 取 poi_id，再 maps_search_detail(id=poi_id) 得到 海口东站坐标 destination_station='110.342865,19.983409'。计算：
- 直接A->B：maps_driving_by_coordinates(origin='110.339964,20.061153', destination='110.342865,19.983409') 得到 t_direct=1085秒。
- 绕行A->P->B：A->P复用步骤3 t_AP=121秒；再调用 maps_driving_by_coordinates(origin='110.341070,20.058308', destination='110.342865,19.983409') 得到 t_PB=1178秒；t_detour=t_AP+t_PB=1299秒。
- 验证 ｜t_detour - t_direct｜ = 214秒 = 3.57分钟 ≤4分钟。
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
    maps_text_search,
    maps_search_detail ,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.339964,20.061153",
    search_radius: int = 2000,
    keywords: str = "公共厕所",
    min_poi_count: int = 8,
    max_driving_distance: int = 2000,  # 2 km = 2000 meters
    max_walking_distance: int = 1200,  # 1200 meters
    max_time_difference: int = 720,  # 12 minutes = 720 seconds
    bus_stop_search_radius: int = 600,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_duration: int = 720,  # 12 minutes = 720 seconds
    station_name: str = "海口东站",
    city: str = "海口",
    max_detour_increment: int = 240  # 4 minutes = 240 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近2000米内：调用 maps_around_search，验证返回pois数量≥8，且包含目标POI。
    2) POI类型：从步骤1的pois中读取该POI名称/关键词匹配"公共厕所"，并可辅以 maps_search_detail 确认。
    3) 到出发地最大驾车距离（公里）：调用 maps_search_detail 取location，调用 maps_driving_by_coordinates，验证 ≤2000米。
    4) 到出发地最大步行距离（米）：调用 maps_walking_by_coordinates，验证 ≤1200米。
    5) 两种方式通行时间差值绝对值 < 12分钟：复用步骤3的驾车时长、步骤4的步行时长，计算差值绝对值，验证 <720秒。
    6) 厕所附近600米内最近公交站步行时间≤12分钟：调用 maps_around_search 获取公交站，对每个公交站调用 maps_walking_by_coordinates，取最小值，验证 ≤720秒。
    7) 绕行增加时间不超过4分钟：调用获取海口东站坐标，计算直接路线和绕行路线的时间差，验证 ≤240秒。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"110.339964,20.061153"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"公共厕所"
        min_poi_count: 最小POI数量，默认8
        max_driving_distance: 最大驾车距离（米），默认2000
        max_walking_distance: 最大步行距离（米），默认1200
        max_time_difference: 最大时间差（秒），默认720（12分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认600
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认720（12分钟）
        station_name: 车站名称，默认"海口东站"
        city: 城市名称，默认"海口"
        max_detour_increment: 最大绕行增加时间（秒），默认240（4分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2000米内
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

    # 验证POI数量≥8
    poi_count = len(around_search_result.pois)
    if poi_count < min_poi_count:
        print(f"❌ 找到{poi_count}个POI，少于{min_poi_count}个")
        return False
    print(f"✅ 找到{poi_count}个POI，符合要求（>= {min_poi_count}个）")

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

    # 步骤2: 获取目标POI详情
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 到出发地最大驾车距离≤2000米
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_distance = driving_result.total_distance_meters
    driving_duration = driving_result.total_duration_seconds
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")
    print(f"✅ 驾车时长{driving_duration}秒")

    # 步骤4: 到出发地最大步行距离≤1200米
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_distance = walking_result.total_distance_meters
    walking_duration = walking_result.total_duration_seconds
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米）")
    print(f"✅ 步行时长{walking_duration}秒")

    # 步骤5: 两种方式通行时间差值绝对值 < 12分钟
    time_difference = abs(walking_duration - driving_duration)
    if time_difference >= max_time_difference:
        print(f"❌ 步行和驾车时间差{time_difference}秒（{time_difference / 60:.2f}分钟），不小于{max_time_difference}秒（{max_time_difference // 60}分钟）")
        return False
    print(f"✅ 步行和驾车时间差{time_difference}秒（{time_difference / 60:.2f}分钟），符合要求（< {max_time_difference}秒，即{max_time_difference // 60}分钟）")

    # 步骤6: 厕所附近600米内最近公交站步行时间≤12分钟
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False

    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")

    # 计算到每个公交站的步行时间，找到最小值
    min_bus_stop_walking_duration = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        bus_stop_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=bus_stop.location
        )
        if bus_stop_walking_result.error or bus_stop_walking_result.total_duration_seconds is None:
            continue

        duration = bus_stop_walking_result.total_duration_seconds
        if min_bus_stop_walking_duration is None or duration < min_bus_stop_walking_duration:
            min_bus_stop_walking_duration = duration

    if min_bus_stop_walking_duration is None:
        print(f"❌ 无法计算到公交站的步行时间")
        return False

    if min_bus_stop_walking_duration > max_bus_stop_walking_duration:
        print(f"❌ 到最近公交站步行时长{min_bus_stop_walking_duration}秒，超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到最近公交站步行时长{min_bus_stop_walking_duration}秒，符合要求（<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    # 步骤7: 绕行增加时间不超过4分钟
    # 获取海口东站坐标
    station_text_result = maps_text_search(keywords=station_name, city=city)
    if station_text_result.error:
        print(f"❌ 获取{station_name}坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到{station_name}坐标")
        return False

    first_poi_id = station_text_result.pois[0].id

    station_detail_result = maps_search_detail(id=first_poi_id)

    if station_detail_result.error:

        print(f"❌ 获取坐标失败: {station_detail_result.error}")

        return False

    if not station_detail_result.location:

        print("❌ 未获取到坐标")

        return False

    station_location = station_detail_result.location
    print(f"✅ 获取{station_name}坐标: {station_location}")

    # 计算直接路线：A->B
    direct_driving_result = maps_driving_by_coordinates(origin=user_location, destination=station_location)
    if direct_driving_result.error:
        print(f"❌ 计算直接路线失败: {direct_driving_result.error}")
        return False

    if direct_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取直接路线时长")
        return False

    direct_duration = direct_driving_result.total_duration_seconds
    print(f"✅ 直接路线时长{direct_duration}秒")

    # 计算绕行路线：A->P->B
    # A->P 已经在步骤3计算过，复用 driving_duration
    # 计算 P->B
    detour_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if detour_driving_result.error:
        print(f"❌ 计算绕行路线(P->B)失败: {detour_driving_result.error}")
        return False

    if detour_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取绕行路线(P->B)时长")
        return False

    detour_pb_duration = detour_driving_result.total_duration_seconds
    detour_total_duration = driving_duration + detour_pb_duration
    print(f"✅ 绕行路线时长{detour_total_duration}秒（A->P: {driving_duration}秒 + P->B: {detour_pb_duration}秒）")

    # 计算绕行增加时间
    detour_increment = abs(detour_total_duration - direct_duration)
    if detour_increment > max_detour_increment:
        print(f"❌ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），超过{max_detour_increment}秒（{max_detour_increment // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），符合要求（<= {max_detour_increment}秒，即{max_detour_increment // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 810.py 文件...\n")
    result = verify_poi(poi_id="B0FFHIQX6V")
    print(f"\n验证结果: {result}")


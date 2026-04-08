"""
输入：B0L2UUECYH
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米以内（周边搜索硬约束）
- 调用 maps_around_search(location='115.362422,22.782599', radius='2000', keywords='电竞馆')
- 验证返回的pois中包含 target_poi_id='B0L2UUECYH'

2) 从用户位置步行到店的距离 ≤1500米
- 调用 maps_search_detail(id='B0L2UUECYH') 获取目标POI坐标 dest
- 调用 maps_walking_by_coordinates(origin='115.362422,22.782599', destination=dest)
- 验证 total_distance_meters ≤ 1500

3) 朋友从汕尾站开车到店：驾车距离 ≤8公里
- 调用 maps_search_detail(id='B02940MWIU') 获取汕尾站坐标 swz
- 调用 maps_driving_by_coordinates(origin=swz, destination=dest)
- 验证 total_distance_meters ≤ 8000

4) 店到公交站：在店周边800米内找公交站，并以“最近直线距离”的那个站作为比较对象
- 调用 maps_around_search(location=dest, radius='800', keywords='公交站') 得到公交站列表 stops
- 对每个 stop.location 调用 maps_distance(origins=dest, destination=stop.location)，取最小直线距离 d_min 及对应站点 stop_min
- 验证 d_min ≤ 150

5) 店走到上述最近直线距离公交站：步行时间 ≤12分钟
- 调用 maps_walking_by_coordinates(origin=dest, destination=stop_min.location)
- 验证 total_duration_seconds ≤ 720

6) 店开车到汕尾站：驾车时间 ≤16分钟
- 调用 maps_driving_by_coordinates(origin=dest, destination=swz)
- 验证 total_duration_seconds ≤ 960

"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates,
    maps_geo,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B0L2UUECYH",
    user_location: str = "115.362422,22.782599",
    radius: str = "2000",
    keywords: str = "电竞馆",
    max_walking_distance: int = 1500,
    shanwei_station_poi_id: str = "B02940MWIU",
    max_driving_distance: int = 8000,
    bus_search_radius: str = "800",
    bus_keywords: str = "公交站",
    max_bus_distance: int = 150,
    max_bus_walking_time: int = 720,
    max_station_driving_time: int = 960
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_walking_distance: 最大步行距离（米）
        shanwei_station_poi_id: 汕尾站POI ID
        max_driving_distance: 最大驾车距离（米）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_bus_distance: 到公交站的最大直线距离（米）
        max_bus_walking_time: 到公交站的最大步行时间（秒）
        max_station_driving_time: 到汕尾站的最大驾车时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近2000米以内（周边搜索硬约束）
    print(f"步骤1: 验证附近{radius}米内的周边搜索约束 - 查询POI ID: {target_poi_id}")
    around_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )

    if around_result.error:
        print(f"步骤1失败: {around_result.error}")
        return False

    if not around_result.pois:
        print("步骤1失败: 未找到任何POI")
        return False

    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'")

    # 获取POI坐标（后续步骤需要）
    print(f"\n获取POI坐标 - 查询POI ID: {target_poi_id}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"获取POI坐标失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print("获取POI坐标失败: 未获取到POI坐标")
        return False

    poi_location = poi_detail.location
    print(f"POI坐标: {poi_location}")

    # 步骤2: 从用户位置步行到店的距离 ≤1500米
    print(f"\n步骤2: 验证步行距离不超过{max_walking_distance}米")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if walking_result.error:
        print(f"步骤2失败: {walking_result.error}")
        all_passed = False
    else:
        if walking_result.total_distance_meters is None:
            print("步骤2失败: 未获取到步行距离")
            all_passed = False
        else:
            walking_distance = walking_result.total_distance_meters
            if walking_distance > max_walking_distance:
                print(f"步骤2失败: 步行距离{walking_distance}米超过要求{max_walking_distance}米")
                all_passed = False
            else:
                print(f"步骤2通过: 步行距离{walking_distance}米，满足要求（<={max_walking_distance}米）")

    # 获取汕尾站坐标（步骤3和步骤6需要）
    print(f"\n获取汕尾站坐标 - 查询POI ID: {shanwei_station_poi_id}")
    station_detail = maps_search_detail(id=shanwei_station_poi_id)

    if station_detail.error:
        print(f"获取汕尾站坐标失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print("获取汕尾站坐标失败: 未获取到汕尾站坐标")
        return False

    station_location = station_detail.location
    print(f"汕尾站坐标: {station_location}")

    # 步骤3: 朋友从汕尾站开车到店：驾车距离 ≤8公里
    print(f"\n步骤3: 验证从{shanwei_station_poi_id}到POI的驾车距离不超过{max_driving_distance}米")
    driving_result = maps_driving_by_coordinates(
        origin=station_location,
        destination=poi_location
    )

    if driving_result.error:
        print(f"步骤3失败: {driving_result.error}")
        all_passed = False
    else:
        if driving_result.total_distance_meters is None:
            print("步骤3失败: 未获取到驾车距离")
            all_passed = False
        else:
            driving_distance = driving_result.total_distance_meters
            if driving_distance > max_driving_distance:
                print(f"步骤3失败: 驾车距离{driving_distance}米超过要求{max_driving_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 驾车距离{driving_distance}米，满足要求（<={max_driving_distance}米）")

    # 步骤4和5需要公交站信息，先搜索公交站
    print(f"\n搜索POI附近{bus_search_radius}米的{bus_keywords}")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"公交站搜索失败: {bus_around_result.error}")
        print("步骤4失败: 无法获取公交站信息")
        print("步骤5失败: 无法获取公交站信息")
        all_passed = False
        bus_pois = []
    else:
        bus_pois = bus_around_result.pois if bus_around_result.pois else []
        bus_count = len(bus_pois)
        print(f"找到{bus_count}个{bus_keywords}")

    # 步骤4: 店到公交站：在店周边800米内找公交站，并以"最近直线距离"的那个站作为比较对象
    print(f"\n步骤4: 验证到{bus_keywords}的最小直线距离不超过{max_bus_distance}米")
    if not bus_pois:
        print("步骤4失败: 未找到任何公交站")
        all_passed = False
        nearest_bus_location = None
    else:
        # 计算到每个公交站的直线距离，找到最小值
        min_distance = float('inf')
        nearest_bus_location = None
        for bus_poi in bus_pois:
            if not bus_poi.location:
                continue

            distance_result = maps_distance(
                origins=poi_location,
                destination=bus_poi.location
            )

            if distance_result.error or not distance_result.results or len(distance_result.results) == 0:
                continue

            distance = distance_result.results[0].distance_meters
            if distance < min_distance:
                min_distance = distance
                nearest_bus_location = bus_poi.location

        if min_distance == float('inf'):
            print("步骤4失败: 无法计算到任何公交站的距离")
            all_passed = False
            nearest_bus_location = None
        elif min_distance > max_bus_distance:
            print(f"步骤4失败: 到最近公交站的距离{min_distance}米超过要求{max_bus_distance}米")
            all_passed = False
        else:
            print(f"步骤4通过: 到最近公交站的距离{min_distance}米，满足要求（<={max_bus_distance}米）")

    # 步骤5: 店走到上述最近直线距离公交站：步行时间 ≤12分钟
    print(f"\n步骤5: 验证到最近{bus_keywords}的步行时间不超过{max_bus_walking_time}秒（{max_bus_walking_time//60}分钟）")
    if nearest_bus_location is None:
        print("步骤5失败: 未获取到最近公交站坐标")
        all_passed = False
    else:
        walking_to_bus_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=nearest_bus_location
        )

        if walking_to_bus_result.error:
            print(f"步骤5失败: 计算步行时间失败 - {walking_to_bus_result.error}")
            all_passed = False
        else:
            if walking_to_bus_result.total_duration_seconds is None:
                print("步骤5失败: 未获取到步行时间")
                all_passed = False
            else:
                walking_time = walking_to_bus_result.total_duration_seconds
                if walking_time > max_bus_walking_time:
                    print(f"步骤5失败: 步行时间{walking_time}秒超过要求{max_bus_walking_time}秒")
                    all_passed = False
                else:
                    print(f"步骤5通过: 步行时间{walking_time}秒，满足要求（<={max_bus_walking_time}秒）")

    # 步骤6: 店开车到汕尾站：驾车时间 ≤16分钟
    print(f"\n步骤6: 验证到{shanwei_station_poi_id}的驾车时间不超过{max_station_driving_time}秒（{max_station_driving_time//60}分钟）")
    station_driving_result = maps_driving_by_coordinates(
        origin=poi_location,
        destination=station_location
    )

    if station_driving_result.error:
        print(f"步骤6失败: {station_driving_result.error}")
        all_passed = False
    else:
        if station_driving_result.total_duration_seconds is None:
            print("步骤6失败: 未获取到驾车时间")
            all_passed = False
        else:
            driving_time = station_driving_result.total_duration_seconds
            if driving_time > max_station_driving_time:
                print(f"步骤6失败: 驾车时间{driving_time}秒超过要求{max_station_driving_time}秒")
                all_passed = False
            else:
                print(f"步骤6通过: 驾车时间{driving_time}秒，满足要求（<={max_station_driving_time}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()

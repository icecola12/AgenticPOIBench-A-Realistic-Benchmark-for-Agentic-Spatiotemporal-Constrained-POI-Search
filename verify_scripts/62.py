
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束：调用 maps_around_search(location='123.757709,41.296171', radius='2000', keywords='酒店')，验证返回pois中包含目标poi_id=B0L2FP1YFP。
2) 评分约束：调用 maps_search_detail(id='B0L2FP1YFP')，读取biz_ext.rating，验证 rating>=4.8。
3) 最大骑行时间：从 maps_search_detail 获取酒店location=123.760372,41.296026；调用 maps_bicycling_by_coordinates(origin='123.757709,41.296171', destination='123.760372,41.296026')，验证 total_duration_seconds<=480。
4) 到客运站最大驾车时间：调用 maps_search_detail(id='B019E00401') 获取本溪长客中心站location=123.772243,41.311857（entr_location=123.772874,41.312149亦可，验证时固定用entr_location）；调用 maps_driving_by_coordinates(origin='123.760372,41.296026', destination='123.772874,41.312149')，验证 total_duration_seconds<=600。
5) 双点通行时间差：
a. 调用 maps_search_detail(id='B019E006JR') 获取本溪站entr_location=123.760472,41.295710；调用 maps_walking_by_coordinates(origin='123.760472,41.295710', destination='123.760372,41.296026') 得到t_walk。
b. 调用 maps_driving_by_coordinates(origin='123.772874,41.312149', destination='123.760372,41.296026') 得到t_drive。
c. 验证 |t_walk - t_drive| <= 240秒。
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
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "123.757709,41.296171",
    search_radius: int = 2000,  # 2km
    keywords: str = "酒店",
    min_rating: float = 4.8,
    max_bicycling_duration: int = 480,  # 8 minutes = 480 seconds
    bus_station_id: str = "B019E00401",
    max_driving_duration: int = 600,  # 10 minutes = 600 seconds
    train_station_id: str = "B019E006JR",
    max_time_difference: int = 240  # 4 minutes = 240 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边约束：调用 maps_around_search，验证返回pois中包含目标poi_id
    2) 评分约束：调用 maps_search_detail，验证 rating>=4.8
    3) 最大骑行时间：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds<=480
    4) 到客运站最大驾车时间：调用 maps_search_detail 获取客运站坐标，调用 maps_driving_by_coordinates，验证 total_duration_seconds<=600
    5) 双点通行时间差：验证 |t_walk - t_drive| <= 240秒

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"123.757709,41.296171"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最低评分，默认4.8
        max_bicycling_duration: 最大骑行时长（秒），默认480（8分钟）
        bus_station_id: 客运站POI ID，默认"B019E00401"
        max_driving_duration: 最大驾车时长（秒），默认600（10分钟）
        train_station_id: 火车站POI ID，默认"B019E006JR"
        max_time_difference: 最大时间差（秒），默认240（4分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边约束验证（2公里内的酒店）
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

    # 步骤2: 获取目标POI详情并验证评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    hotel_location = poi_detail.location
    print(f"✅ 获取酒店坐标: {hotel_location}")

    # 评分验证（rating >= 4.8）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = poi_detail.biz_ext['rating']
        try:
            rating_value = float(rating)
            if rating_value < min_rating:
                print(f"❌ 评分{rating_value}低于{min_rating}")
                return False
            print(f"✅ 评分{rating_value}，符合要求（>= {min_rating}）")
        except (ValueError, TypeError):
            print(f"⚠️  无法解析评分值: {rating}，跳过评分验证")
    else:
        print(f"⚠️  未找到评分信息，跳过评分验证")

    # 步骤3: 最大骑行时间验证（<= 8分钟）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=hotel_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False

    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")

    # 步骤4: 获取客运站坐标并验证驾车时间
    bus_station_detail = maps_search_detail(id=bus_station_id)
    if bus_station_detail.error:
        print(f"❌ 获取客运站详情失败: {bus_station_detail.error}")
        return False

    # 优先使用entr_location，如果没有则使用location
    if bus_station_detail.entr_location:
        bus_station_location = bus_station_detail.entr_location
        print(f"✅ 获取客运站入口坐标: {bus_station_location}")
    elif bus_station_detail.location:
        bus_station_location = bus_station_detail.location
        print(f"✅ 获取客运站坐标: {bus_station_location}")
    else:
        print(f"❌ 客运站没有location信息")
        return False

    # 驾车时间验证（<= 10分钟）
    driving_result = maps_driving_by_coordinates(origin=hotel_location, destination=bus_station_location)
    if driving_result.error:
        print(f"❌ 计算到客运站驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到客运站驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到客运站驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到客运站驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤5: 双点通行时间差验证
    # 5a. 获取火车站坐标并计算步行时间
    train_station_detail = maps_search_detail(id=train_station_id)
    if train_station_detail.error:
        print(f"❌ 获取火车站详情失败: {train_station_detail.error}")
        return False

    if train_station_detail.entr_location:
        train_station_location = train_station_detail.entr_location
        print(f"✅ 获取火车站入口坐标: {train_station_location}")
    elif train_station_detail.location:
        train_station_location = train_station_detail.location
        print(f"✅ 获取火车站坐标: {train_station_location}")
    else:
        print(f"❌ 火车站没有location信息")
        return False

    walking_result = maps_walking_by_coordinates(origin=train_station_location, destination=hotel_location)
    if walking_result.error:
        print(f"❌ 计算从火车站步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取从火车站步行时长")
        return False

    t_walk = walking_result.total_duration_seconds
    print(f"✅ 从火车站步行时长: {t_walk}秒")

    # 5b. 计算从客运站驾车时间
    driving_result_2 = maps_driving_by_coordinates(origin=bus_station_location, destination=hotel_location)
    if driving_result_2.error:
        print(f"❌ 计算从客运站驾车路线失败: {driving_result_2.error}")
        return False

    if driving_result_2.total_duration_seconds is None:
        print(f"❌ 无法获取从客运站驾车时长")
        return False

    t_drive = driving_result_2.total_duration_seconds
    print(f"✅ 从客运站驾车时长: {t_drive}秒")

    # 5c. 验证时间差
    time_difference = abs(t_walk - t_drive)
    if time_difference > max_time_difference:
        print(f"❌ 时间差{time_difference}秒，超过{max_time_difference}秒（{max_time_difference // 60}分钟）")
        return False
    print(f"✅ 时间差{time_difference}秒，符合要求（<= {max_time_difference}秒，即{max_time_difference // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 630.py 文件...\n")
    result = verify_poi(poi_id="B0L2FP1YFP")
    print(f"\n验证结果: {result}")

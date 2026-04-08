"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
🔍 验证方法 (verification_method):

我将按照四个步骤进行验证：  
1) 周边与类型：调用 maps_around_search(location="117.19938,34.214706", radius="2000", keywords="诊所")，验证返回结果中包含 poi_id="B02040TZE4"。  
2) 骑行时长（用户->诊所）：调用 maps_search_detail(id="B02040TZE4")获取诊所坐标 destination；再调用 maps_bicycling_by_coordinates(origin="117.19938,34.214706", destination=destination)，验证 total_duration_seconds<=480（8分钟）。  
3) 时间差约束（朋友->诊所 vs 用户->诊所，均为骑行）：调用 maps_geo(address="中国矿业大学南湖校区", city="徐州")获取朋友起点坐标 origin_friend（取第一条结果 location="117.144521,34.215107"）；分别调用 maps_bicycling_by_coordinates(origin=origin_friend, destination=destination) 与步骤2的骑行结果，令 t_friend 与 t_user 为两者 total_duration_seconds，验证 |t_friend - t_user| <= 600（10分钟）。  
4) 枢纽可达性与公交站：  
4.1 调用 maps_geo(address="徐州东站", city="徐州") 得到徐州东站坐标 dest_station（location="117.306044,34.267951"）；调用 maps_driving_by_coordinates(origin=destination, destination=dest_station)，验证 total_duration_seconds<=2400（40分钟）。  
4.2 调用 maps_around_search(location=destination, radius="300", keywords="公交站")，验证返回 pois 数量>=1（例如包含"翟山地铁站(公交站)"）。
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
    maps_geo,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.19938,34.214706",
    search_radius: int = 2000,  # 2km
    keywords: str = "诊所",
    max_bicycling_duration: int = 8 * 60,  # 8分钟 = 480秒
    friend_start_address: str = "中国矿业大学南湖校区",
    friend_start_city: str = "徐州",
    max_time_diff: int = 10 * 60,  # 10分钟 = 600秒
    station_address: str = "徐州东站",
    station_city: str = "徐州",
    max_driving_duration: int = 40 * 60,  # 40分钟 = 2400秒
    bus_station_search_radius: int = 300,  # 300米
    bus_station_keywords: str = "公交站",
    min_bus_station_count: int = 1  # 至少1个公交站
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 周边与类型：调用 maps_around_search，验证返回结果中包含目标poi_id。
    2) 骑行时长（用户->诊所）：调用 maps_search_detail 获取诊所坐标；再调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 480（8分钟）。
    3) 时间差约束（朋友->诊所 vs 用户->诊所，均为骑行）：调用 maps_geo 获取朋友起点坐标；分别调用 maps_bicycling_by_coordinates，验证 |t_friend - t_user| <= 600（10分钟）。
    4) 枢纽可达性与公交站：
       4.1 调用 maps_geo 得到徐州东站坐标；调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 2400（40分钟）。
       4.2 调用 maps_around_search 在诊所周边300米搜索公交站，验证返回 pois 数量 >= 1。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.19938,34.214706"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"诊所"
        max_bicycling_duration: 最大骑行时长（秒），默认480（8分钟）
        friend_start_address: 朋友起点地址，默认"中国矿业大学南湖校区"
        friend_start_city: 朋友起点所在城市，默认"徐州"
        max_time_diff: 最大时间差（秒），默认600（10分钟）
        station_address: 火车站地址，默认"徐州东站"
        station_city: 火车站所在城市，默认"徐州"
        max_driving_duration: 最大驾车时长（秒），默认2400（40分钟）
        bus_station_search_radius: 公交站搜索半径（米），默认300
        bus_station_keywords: 公交站搜索关键词，默认"公交站"
        min_bus_station_count: 最少公交站数量，默认1
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边与类型 - 验证POI在用户周边2km内
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
    
    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")
    
    # 步骤2: 骑行时长（用户->诊所） - 验证用户到诊所的骑行时长不超过8分钟
    user_bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if user_bicycling_result.error:
        print(f"❌ 计算用户到诊所的骑行路线失败: {user_bicycling_result.error}")
        return False
    
    if user_bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取用户到诊所的骑行时长")
        return False
    
    user_bicycling_duration = user_bicycling_result.total_duration_seconds
    if user_bicycling_duration > max_bicycling_duration:
        print(f"❌ 用户到诊所的骑行时长{user_bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 用户到诊所的骑行时长{user_bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    
    # 步骤3: 时间差约束 - 验证朋友到诊所与用户到诊所的骑行时间差不超过10分钟
    friend_geo_result = maps_geo(address=friend_start_address, city=friend_start_city)
    if friend_geo_result.error:
        print(f"❌ 获取朋友起点坐标失败: {friend_geo_result.error}")
        return False
    
    if not friend_geo_result.results or len(friend_geo_result.results) == 0:
        print(f"❌ 未找到朋友起点坐标")
        return False
    
    # 使用第一条记录作为朋友起点坐标
    friend_location = friend_geo_result.results[0].location
    print(f"✅ 获取朋友起点坐标: {friend_location} ({friend_geo_result.results[0].formatted_address})")
    
    friend_bicycling_result = maps_bicycling_by_coordinates(origin=friend_location, destination=poi_location)
    if friend_bicycling_result.error:
        print(f"❌ 计算朋友到诊所的骑行路线失败: {friend_bicycling_result.error}")
        return False
    
    if friend_bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取朋友到诊所的骑行时长")
        return False
    
    friend_bicycling_duration = friend_bicycling_result.total_duration_seconds
    time_diff = abs(friend_bicycling_duration - user_bicycling_duration)
    
    if time_diff > max_time_diff:
        print(f"❌ 骑行时间差{time_diff}秒，超过{max_time_diff}秒（{max_time_diff // 60}分钟）")
        print(f"   用户到诊所: {user_bicycling_duration}秒（{user_bicycling_duration // 60}分钟）")
        print(f"   朋友到诊所: {friend_bicycling_duration}秒（{friend_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时间差{time_diff}秒，符合要求（<= {max_time_diff}秒，即{max_time_diff // 60}分钟）")
    print(f"   用户到诊所: {user_bicycling_duration}秒（{user_bicycling_duration // 60}分钟）")
    print(f"   朋友到诊所: {friend_bicycling_duration}秒（{friend_bicycling_duration // 60}分钟）")
    
    # 步骤4: 枢纽可达性与公交站
    # 4.1: 到徐州东站驾车时长约束 - 验证从诊所到徐州东站驾车时间不超过40分钟
    station_geo_result = maps_geo(address=station_address, city=station_city)
    if station_geo_result.error:
        print(f"❌ 获取火车站坐标失败: {station_geo_result.error}")
        return False
    
    if not station_geo_result.results or len(station_geo_result.results) == 0:
        print(f"❌ 未找到火车站坐标")
        return False
    
    # 使用第一条记录作为火车站坐标
    station_location = station_geo_result.results[0].location
    print(f"✅ 获取火车站坐标: {station_location} ({station_geo_result.results[0].formatted_address})")
    
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到火车站驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到火车站驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 4.2: 公交站约束 - 验证诊所周边300米内有公交站
    bus_station_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_station_search_radius),
        keywords=bus_station_keywords
    )
    if bus_station_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_station_search_result.error}")
        return False
    
    bus_station_count = len(bus_station_search_result.pois) if bus_station_search_result.pois else 0
    if bus_station_count < min_bus_station_count:
        print(f"❌ 诊所周边{bus_station_search_radius}米内找到{bus_station_count}个公交站，少于{min_bus_station_count}个")
        return False
    
    print(f"✅ 诊所周边{bus_station_search_radius}米内找到{bus_station_count}个公交站，符合要求（>= {min_bus_station_count}个）")
    if bus_station_search_result.pois:
        print(f"   例如: {bus_station_search_result.pois[0].name}")
    
    print(f"✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python id_554.py <poi_id> [user_location]")
        print("示例: python id_554.py B02040TZE4")
        print("示例: python id_554.py B02040TZE4 117.19938,34.214706")
        print("未传参，使用示例默认值运行。")
        poi_id = "B02040TZE4"
        user_location = "117.19938,34.214706"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "117.19938,34.214706"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("-" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("-" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")

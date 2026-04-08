"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
🔍 验证方法 (verification_method):

1) 距离约束(2km内)：调用 maps_around_search(location="119.662358,29.070169", radius="2000", keywords="酒吧")，验证返回pois中包含目标poi_id=B0LG774AWB。  
2) 评分不低于4.4：对poi_id调用 maps_search_detail(id="B0LG774AWB")，读取biz_ext.rating，验证 rating>=4.4。  
3) 骑行时间<=5分钟：从 maps_search_detail 取目标location=119.661275,29.069975；调用 maps_bicycling_by_coordinates(origin="119.662358,29.070169", destination="119.661275,29.069975")，验证 total_duration_seconds<=300。  
4) 开车到金华站<=12分钟：调用 maps_geo(address="金华站", city="金华") 获取金华站location=119.635860,29.110764；再调用 maps_driving_by_coordinates(origin="119.661275,29.069975", destination="119.635860,29.110764")，验证 total_duration_seconds<=720。  
5) 附近300米内有公交站：先调用 maps_around_search(location=POI坐标, radius="300", keywords="公交站") 获取候选公交站列表，验证列表长度是不是大于0。
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
    user_location: str = "119.662358,29.070169",
    search_radius: int = 2000,  # 2km
    keywords: str = "酒吧",
    min_rating: float = 4.4,
    max_bicycling_duration: int = 5 * 60,  # 5分钟 = 300秒
    station_address: str = "金华站",
    station_city: str = "金华",
        max_driving_duration: int = 12 * 60,  # 12分钟 = 720秒
        bus_station_keywords: str = "公交站",
        max_bus_station_distance: int = 300  # 300米
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 距离约束(2km内)：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 评分不低于4.4：调用 maps_search_detail，读取biz_ext.rating，验证 rating >= 4.4。
    3) 骑行时间<=5分钟：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 300。
    4) 开车到金华站<=12分钟：调用 maps_geo 获取金华站坐标；再调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 720。
    5) 附近300米内有公交站：先调用 maps_around_search(location=POI坐标, radius="300", keywords="公交站") 获取候选公交站列表，验证列表长度是不是大于0。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"119.662358,29.070169"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒吧"
        min_rating: 最低评分，默认4.4
        max_bicycling_duration: 最大骑行时长（秒），默认300（5分钟）
        station_address: 火车站地址，默认"金华站"
        station_city: 火车站所在城市，默认"金华"
        max_driving_duration: 最大驾车时长（秒），默认720（12分钟）
        bus_station_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_station_distance: 公交站搜索半径（米），默认300
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束(2km内) - 验证POI在用户周边2km内
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
    
    # 步骤2: 获取POI详情并验证评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")
    
    # 验证评分
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息，无法验证评分")
        return False
    
    rating = None
    if isinstance(poi_detail.biz_ext, dict):
        rating = poi_detail.biz_ext.get("rating")
    
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False
    
    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ POI的rating值无效: {rating}")
        return False
    
    if rating_value < min_rating:
        print(f"❌ POI评分{rating_value}，低于{min_rating}")
        return False
    print(f"✅ POI评分{rating_value}，符合要求（>= {min_rating}）")
    
    # 步骤3: 骑行时间<=5分钟 - 验证用户到酒吧的骑行时长不超过5分钟
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
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
    
    # 步骤4: 开车到金华站<=12分钟 - 验证从酒吧到金华站驾车时间不超过12分钟
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
    
    # 步骤5: 附近300米内有公交站 - 验证酒吧附近300米内有公交站
    bus_station_search_result = maps_around_search(
        location=poi_location,
        radius=str(max_bus_station_distance),
        keywords=bus_station_keywords
    )
    if bus_station_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_station_search_result.error}")
        return False
    
    bus_station_count = len(bus_station_search_result.pois) if bus_station_search_result.pois else 0
    if bus_station_count == 0:
        print(f"❌ POI周边{max_bus_station_distance}米内未找到公交站")
        return False
    
    print(f"✅ POI周边{max_bus_station_distance}米内找到{bus_station_count}个公交站，符合要求（> 0）")
    if bus_station_search_result.pois:
        print(f"   例如: {bus_station_search_result.pois[0].name}")
    
    print(f"✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python id_566.py <poi_id> [user_location]")
        print("示例: python id_566.py B0LG774AWB")
        print("示例: python id_566.py B0LG774AWB 119.662358,29.070169")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0LG774AWB"
        user_location = "119.662358,29.070169"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "119.662358,29.070169"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("-" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("-" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")

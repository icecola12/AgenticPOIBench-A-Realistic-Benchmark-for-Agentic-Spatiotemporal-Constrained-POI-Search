"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search(location='115.907208,28.706583', radius='5000', keywords='KTV')，验证返回pois中包含 target_poi_id='B0HD35PKLO'。
2) 评分验证：调用 maps_search_detail(id='B0HD35PKLO')，读取 biz_ext.rating，验证 rating >= 4.7。
3) 南昌站坐标获取：调用 maps_text_search(keywords='南昌站', city='南昌', citylimit='true')，取pois中名称为"南昌站"的POI（如 id='B031706310'），再调用 maps_search_detail(id='B031706310') 获取其 location。
4) 去南昌站驾车时长验证：调用 maps_driving_by_coordinates(origin=KTV.location, destination=南昌站.location)，验证 total_duration_seconds <= 360（6分钟）。
5) 远离八一广场距离验证：调用 maps_text_search(keywords='八一广场', city='南昌', citylimit='true')，取pois中名称为"八一广场"的POI（如 id='B031704RAC'），再调用 maps_search_detail(id='B031704RAC') 获取其 location；调用 maps_distance(origins=八一广场.location, destination=KTV.location)，验证 distance_meters >= 1000。
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
    maps_driving_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def find_poi_by_name(text_search_result, target_name: str):
    """
    在文本搜索结果中查找指定名称的POI
    
    Args:
        text_search_result: maps_text_search 返回的结果
        target_name: 目标POI名称
    
    Returns:
        POI对象，如果未找到返回None
    """
    if text_search_result.error:
        return None
    
    if not text_search_result.pois:
        return None
    
    for poi in text_search_result.pois:
        if poi.name == target_name:
            return poi
    
    return None


def verify_poi(
    poi_id: str,
    user_location: str = "115.907208,28.706583",
    search_radius: int = 5000,  # 5km
    keywords: str = "KTV",
    min_rating: float = 4.7,
    station_keywords: str = "南昌站",
    station_city: str = "南昌",
    max_driving_duration: int = 360,  # 6 minutes = 360 seconds
    square_keywords: str = "八一广场",
    square_city: str = "南昌",
    min_distance_meters: int = 1000  # 至少1公里
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 周边范围验证：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 评分验证：调用 maps_search_detail，验证 rating >= 4.7。
    3) 南昌站坐标获取：调用 maps_text_search 找到"南昌站"，再调用 maps_search_detail 获取其 location。
    4) 去南昌站驾车时长验证：调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 360。
    5) 远离八一广场距离验证：调用 maps_text_search 找到"八一广场"，再调用 maps_distance，验证 distance_meters >= 1000。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.907208,28.706583"
        search_radius: 搜索半径（米），默认5000（5公里）
        keywords: 搜索关键词，默认"KTV"
        min_rating: 最小评分，默认4.7
        station_keywords: 车站搜索关键词，默认"南昌站"
        station_city: 车站所在城市，默认"南昌"
        max_driving_duration: 最大驾车时长（秒），默认360（6分钟）
        square_keywords: 广场搜索关键词，默认"八一广场"
        square_city: 广场所在城市，默认"南昌"
        min_distance_meters: 最小距离（米），默认1000（1公里）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（附近5公里内）
    print(f"【步骤1】验证周边可达性（{search_radius}米范围内）")
    print("-" * 80)
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
    print(f"\n【步骤2】验证POI详情和评分")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location} ({poi_detail.name})")
    
    # 验证评分
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息，无法验证评分")
        return False
    
    rating = poi_detail.biz_ext.get("rating")
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False
    
    try:
        rating_float = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析评分: {rating}")
        return False
    
    if rating_float < min_rating:
        print(f"❌ 评分{rating_float}低于要求{min_rating}")
        return False
    print(f"✅ 评分{rating_float}符合要求（>= {min_rating}）")
    
    # 步骤3: 南昌站坐标获取
    print(f"\n【步骤3】获取{station_keywords}坐标")
    print("-" * 80)
    station_search_result = maps_text_search(
        keywords=station_keywords,
        city=station_city,
        citylimit="true"
    )
    if station_search_result.error:
        print(f"❌ 搜索{station_keywords}失败: {station_search_result.error}")
        return False
    
    station_poi = find_poi_by_name(station_search_result, station_keywords)
    if not station_poi:
        print(f"❌ 未找到名称为'{station_keywords}'的POI")
        return False
    
    print(f"✅ 找到{station_keywords}: {station_poi.name} (ID: {station_poi.id})")
    
    station_detail = maps_search_detail(id=station_poi.id)
    if station_detail.error:
        print(f"❌ 获取{station_keywords}详情失败: {station_detail.error}")
        return False
    
    if not station_detail.location:
        print(f"❌ {station_keywords}没有location信息")
        return False
    
    station_location = station_detail.location
    print(f"✅ 获取{station_keywords}坐标: {station_location}")
    
    # 步骤4: 去南昌站驾车时长验证
    print(f"\n【步骤4】验证去{station_keywords}的驾车时间")
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_keywords}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_keywords}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 步骤5: 远离八一广场距离验证
    print(f"\n【步骤5】验证远离{square_keywords}的距离")
    print("-" * 80)
    square_search_result = maps_text_search(
        keywords=square_keywords,
        city=square_city,
        citylimit="true"
    )
    if square_search_result.error:
        print(f"❌ 搜索{square_keywords}失败: {square_search_result.error}")
        return False
    
    square_poi = find_poi_by_name(square_search_result, square_keywords)
    if not square_poi:
        print(f"❌ 未找到名称为'{square_keywords}'的POI")
        return False
    
    print(f"✅ 找到{square_keywords}: {square_poi.name} (ID: {square_poi.id})")
    
    square_detail = maps_search_detail(id=square_poi.id)
    if square_detail.error:
        print(f"❌ 获取{square_keywords}详情失败: {square_detail.error}")
        return False
    
    if not square_detail.location:
        print(f"❌ {square_keywords}没有location信息")
        return False
    
    square_location = square_detail.location
    print(f"✅ 获取{square_keywords}坐标: {square_location}")
    
    # 计算距离
    distance_result = maps_distance(origins=square_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取距离信息")
        return False
    
    distance_meters = distance_result.results[0].distance_meters
    if distance_meters < min_distance_meters:
        print(f"❌ 距离{square_keywords}{distance_meters}米，小于要求{min_distance_meters}米（{min_distance_meters // 1000}公里）")
        return False
    print(f"✅ 距离{square_keywords}{distance_meters}米，符合要求（>= {min_distance_meters}米，即{min_distance_meters // 1000}公里）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 528.py <poi_id> [user_location]")
        print("示例: python 528.py B0HD35PKLO")
        print("示例: python 528.py B0HD35PKLO 115.907208,28.706583")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0HD35PKLO"
        user_location = "115.907208,28.706583"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "115.907208,28.706583"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")

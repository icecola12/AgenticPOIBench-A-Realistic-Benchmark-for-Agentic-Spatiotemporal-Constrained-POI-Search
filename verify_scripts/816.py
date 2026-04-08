
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围约束：调用 maps_around_search(location='118.132417,24.490177', radius='5000', keywords='博物馆')，验证返回pois中包含 id='B025004043'。
2) 评分约束：调用 maps_search_detail(id='B025004043')，取 biz_ext.rating，验证 rating >= 4.7。
3) 指定公交站直线距离约束：
- 调用 maps_search_detail(id='BV10211110') 获取"文化艺术中心(公交站)"坐标L_bus。
- 调用 maps_search_detail(id='B025004043') 获取博物馆坐标L_poi。
- 调用 maps_distance(origins=L_poi, destination=L_bus)，验证直线距离 <= 200米。
4) 附近地铁站最短步行距离约束：
- 调用 maps_search_detail(id='B025004043') 获取L_poi。
- 调用 maps_around_search(location=L_poi, radius='1200', keywords='地铁站') 获取地铁站列表S。
- 对S中每个地铁站s，调用 maps_walking_by_coordinates(origin=L_poi, destination=s.location) 得到步行距离d_s。
- 取 min(d_s)，验证 min(d_s) <= 1000米。
5) 从出发地到目标点最大驾车距离约束：调用 maps_driving_by_coordinates(origin='118.132417,24.490177', destination=L_poi)，验证 total_distance_meters <= 3000米。
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
    maps_distance,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "118.132417,24.490177",
    search_radius: int = 5000,
    keywords: str = "博物馆",
    min_rating: float = 4.7,
    bus_stop_name: str = "文化艺术中心(公交站)",
    city: str = "厦门",
    max_bus_stop_distance: int = 200,  # 200 meters
    subway_search_radius: int = 1200,
    subway_keywords: str = "地铁站",
    max_subway_walking_distance: int = 1000,  # 1000 meters
    max_driving_distance: int = 3000  # 3000 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围约束：调用 maps_around_search，验证返回pois中包含目标POI。
    2) 评分约束：调用 maps_search_detail，取 biz_ext.rating，验证 rating >= 4.7。
    3) 指定公交站直线距离约束：调用 maps_text_search 搜索公交站，调用 maps_search_detail 获取公交站和博物馆坐标，调用 maps_distance，验证直线距离 <= 200米。
    4) 附近地铁站最短步行距离约束：调用 maps_around_search 获取地铁站列表，对每个地铁站调用 maps_walking_by_coordinates，取最小值，验证 <= 1000米。
    5) 从出发地到目标点最大驾车距离约束：调用 maps_driving_by_coordinates，验证 total_distance_meters <= 3000米。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.132417,24.490177"
        search_radius: 搜索半径（米），默认5000
        keywords: 搜索关键词，默认"博物馆"
        min_rating: 最低评分，默认4.7
        bus_stop_name: 公交站名称，默认"文化艺术中心(公交站)"
        city: 城市名称，默认"厦门"
        max_bus_stop_distance: 到公交站最大直线距离（米），默认200
        subway_search_radius: 地铁站搜索半径（米），默认1200
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_subway_walking_distance: 到地铁站最大步行距离（米），默认1000
        max_driving_distance: 最大驾车距离（米），默认3000

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围约束
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

    # 步骤2: 获取目标POI详情（包括坐标和评分）
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
    if poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = float(poi_detail.biz_ext['rating'])
        if rating < min_rating:
            print(f"❌ POI评分{rating}分，低于{min_rating}分")
            return False
        print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")
    else:
        print(f"❌ POI没有评分信息")
        return False

    # 步骤3: 指定公交站直线距离约束
    # 先搜索公交站
    bus_stop_search_result = maps_text_search(
        keywords=bus_stop_name,
        city=city,
        citylimit="true"
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索{bus_stop_name}失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到{bus_stop_name}")
        return False

    # 获取公交站ID
    bus_stop_id = bus_stop_search_result.pois[0].id
    print(f"✅ 找到{bus_stop_name}，ID: {bus_stop_id}")

    # 获取公交站详情以获取坐标
    bus_stop_detail = maps_search_detail(id=bus_stop_id)
    if bus_stop_detail.error:
        print(f"❌ 获取公交站详情失败: {bus_stop_detail.error}")
        return False

    if not bus_stop_detail.location:
        print(f"❌ 公交站没有location信息")
        return False

    bus_stop_location = bus_stop_detail.location
    print(f"✅ 获取公交站坐标: {bus_stop_location}")

    bus_stop_distance_result = maps_distance(origins=poi_location, destination=bus_stop_location)
    if bus_stop_distance_result.error:
        print(f"❌ 计算到公交站距离失败: {bus_stop_distance_result.error}")
        return False

    if not bus_stop_distance_result.results or len(bus_stop_distance_result.results) == 0:
        print(f"❌ 未获取到到公交站的距离信息")
        return False

    bus_stop_distance = bus_stop_distance_result.results[0].distance_meters
    if bus_stop_distance > max_bus_stop_distance:
        print(f"❌ 到公交站直线距离{bus_stop_distance}米，超过{max_bus_stop_distance}米")
        return False
    print(f"✅ 到公交站直线距离{bus_stop_distance}米，符合要求（<= {max_bus_stop_distance}米）")

    # 步骤4: 附近地铁站最短步行距离约束
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False

    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")

    # 计算到每个地铁站的步行距离，找到最小值
    min_subway_walking_distance = None
    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        subway_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=subway.location
        )
        if subway_walking_result.error or subway_walking_result.total_distance_meters is None:
            continue

        distance = subway_walking_result.total_distance_meters
        if min_subway_walking_distance is None or distance < min_subway_walking_distance:
            min_subway_walking_distance = distance

    if min_subway_walking_distance is None:
        print(f"❌ 无法计算到地铁站的步行距离")
        return False

    if min_subway_walking_distance > max_subway_walking_distance:
        print(f"❌ 到最近地铁站步行距离{min_subway_walking_distance}米，超过{max_subway_walking_distance}米")
        return False
    print(f"✅ 到最近地铁站步行距离{min_subway_walking_distance}米，符合要求（<= {max_subway_walking_distance}米）")

    # 步骤5: 从出发地到目标点最大驾车距离约束
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 816.py 文件...\n")
    result = verify_poi(poi_id="B025004043")
    print(f"\n验证结果: {result}")


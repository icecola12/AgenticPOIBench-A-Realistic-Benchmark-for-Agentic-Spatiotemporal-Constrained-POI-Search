"""
输入：B0FFIB50IY
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束(附近2km)：调用 maps_around_search(location="117.197637,34.223561", radius="2000", keywords="咖啡馆")，验证返回pois中包含 target_poi_id = B0FFIB50IY。
2) 获取目标POI细节与评分：调用 maps_search_detail(id="B0FFIB50IY")，读取biz_ext.rating，验证 rating >= 4.6，并取其location作为poi_loc。
3) 离“淮塔东路2号”直线距离：调用 maps_text_search(keywords="淮塔东路2号", city="徐州") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 取得addr_loc；再调用 maps_distance(origins=poi_loc, destination=addr_loc) 验证 distance_meters <= 2000。
4) 到徐州东站驾车时间：调用 maps_text_search(keywords="徐州东站", city="徐州") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到xzd_loc；调用 maps_driving_by_coordinates(origin=poi_loc, destination=xzd_loc) 验证 total_duration_seconds <= 1200(20分钟)。
5) 200米内有地铁站：调用 maps_around_search(location=poi_loc, radius="200", keywords="地铁站")，验证返回pois非空(至少1个)。
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
    target_poi_id: str = "B0FFIB50IY",
    user_location: str = "117.197637,34.223561",
    around_search_radius: str = "2000",
    around_search_keywords: str = "咖啡馆",
    min_rating: float = 4.6,
    address_name: str = "淮塔东路2号",
    address_city: str = "徐州",
    address_location: str = "117.203519,34.236756",
    max_distance_to_address_meters: int = 2000,
    station_address: str = "徐州东站",
    station_city: str = "徐州",
    station_location: str = "117.306044,34.267951",
    max_driving_duration_seconds: int = 1200,
    metro_search_radius: str = "200",
    metro_search_keywords: str = "地铁站",
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    验证步骤：
    1) 距离约束(附近2km)：验证返回pois中包含target_poi_id
    2) 获取目标POI细节与评分：验证rating >= 4.6，并获取location作为poi_loc
    3) 离"淮塔东路2号"直线距离：验证distance_meters <= 2000
    4) 到徐州东站驾车时间：验证total_duration_seconds <= 1200(20分钟)
    5) 200米内有地铁站：验证返回pois非空(至少1个)
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        min_rating: 最低评分要求
        address_name: 地址名称
        address_city: 地址所在城市
        address_location: 地址位置坐标（如果maps_text_search+maps_search_detail获取失败则使用此默认值）
        max_distance_to_address_meters: 到地址的最大直线距离（米）
        station_address: 车站地址
        station_city: 车站所在城市
        station_location: 车站位置坐标（如果maps_text_search+maps_search_detail获取失败则使用此默认值）
        max_driving_duration_seconds: 最大驾车时间（秒）
        metro_search_radius: 地铁站搜索半径
        metro_search_keywords: 地铁站搜索关键词
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 5
    
    # 实际用于后续计算的POI坐标，优先使用POI详情中的location
    poi_loc = None
    
    # 验证步骤1: 距离约束(附近2km)
    print("验证步骤1: 距离约束(附近2km)")
    print(f"调用 maps_around_search(location=\"{user_location}\", radius=\"{around_search_radius}\", keywords=\"{around_search_keywords}\")")
    around_result = maps_around_search(
        location=user_location,
        radius=around_search_radius,
        keywords=around_search_keywords
    )
    
    if around_result.error:
        print(f"周边搜索失败: {around_result.error}")
        print("验证步骤1: 未通过")
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break
        
        if poi_found:
            print(f"验证步骤1: 通过 - 在周边搜索结果中找到目标POI ID: {target_poi_id}")
            passed_count += 1
        else:
            print(f"验证步骤1: 未通过 - 在周边搜索结果中未找到目标POI ID: {target_poi_id}")
    
    # 验证步骤2: 获取目标POI细节与评分
    print("\n验证步骤2: 获取目标POI细节与评分")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤2: 未通过")
    else:
        # 获取rating
        rating = None
        if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
            rating_value = detail_result.biz_ext.get("rating")
            if rating_value is not None:
                try:
                    rating = float(rating_value)
                except (ValueError, TypeError):
                    pass
        
        if rating is not None:
            if rating >= min_rating:
                print(f"验证步骤2: 通过 - POI评分 {rating} >= {min_rating}")
                passed_count += 1
            else:
                print(f"验证步骤2: 未通过 - POI评分 {rating} < {min_rating}")
        else:
            print("验证步骤2: 未通过 - 无法获取POI评分信息")
        
        # 获取POI location
        if detail_result.location:
            poi_loc = detail_result.location
            print(f"从POI详情获取到location: {poi_loc}")
        else:
            print("验证步骤2: 警告 - 无法获取POI location")
    
    # 验证步骤3: 离"淮塔东路2号"直线距离
    print("\n验证步骤3: 离\"淮塔东路2号\"直线距离")
    if not poi_loc:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法计算直线距离")
    else:
        print(f"调用 maps_text_search(keywords=\"{address_name}\", city=\"{address_city}\") 获取 poi_id，再 maps_search_detail 获取坐标")
        text_search_result = maps_text_search(keywords=address_name, city=address_city)
        addr_loc = address_location  # 默认使用提供的坐标
        if text_search_result.error:
            print(f"文本搜索失败: {text_search_result.error}")
            print(f"使用默认坐标: {addr_loc}")
        elif not text_search_result.pois or len(text_search_result.pois) == 0:
            print(f"未找到\"淮塔东路2号\"坐标，使用默认坐标: {addr_loc}")
        else:
            first_poi_id = text_search_result.pois[0].id
            detail_result = maps_search_detail(id=first_poi_id)
            if detail_result.error or not detail_result.location:
                print(f"获取详情失败，使用默认坐标: {addr_loc}")
            else:
                addr_loc = detail_result.location
                print(f"获取到\"淮塔东路2号\"坐标: {addr_loc}")
        
        print(f"调用 maps_distance(origins={poi_loc}, destination={addr_loc})")
        distance_result = maps_distance(
            origins=poi_loc,
            destination=addr_loc
        )
        
        if distance_result.error:
            print(f"距离计算失败: {distance_result.error}")
            print("验证步骤3: 未通过")
        else:
            if distance_result.results and len(distance_result.results) > 0:
                distance_meters = distance_result.results[0].distance_meters
                if distance_meters <= max_distance_to_address_meters:
                    print(f"验证步骤3: 通过 - 直线距离 {distance_meters}米 <= {max_distance_to_address_meters}米")
                    passed_count += 1
                else:
                    print(f"验证步骤3: 未通过 - 直线距离 {distance_meters}米 > {max_distance_to_address_meters}米")
            else:
                print("验证步骤3: 未通过 - 未获取到距离结果")
    
    # 验证步骤4: 到徐州东站驾车时间
    print("\n验证步骤4: 到徐州东站驾车时间")
    if not poi_loc:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        print(f"调用 maps_text_search(keywords=\"{station_address}\", city=\"{station_city}\") 获取 poi_id，再 maps_search_detail 获取坐标")
        text_search_result = maps_text_search(keywords=station_address, city=station_city)
        xzd_loc = station_location  # 默认使用提供的坐标
        if text_search_result.error:
            print(f"文本搜索失败: {text_search_result.error}")
            print(f"使用默认坐标: {xzd_loc}")
        elif not text_search_result.pois or len(text_search_result.pois) == 0:
            print(f"未找到徐州东站坐标，使用默认坐标: {xzd_loc}")
        else:
            first_poi_id = text_search_result.pois[0].id
            detail_result = maps_search_detail(id=first_poi_id)
            if detail_result.error or not detail_result.location:
                print(f"获取详情失败，使用默认坐标: {xzd_loc}")
            else:
                xzd_loc = detail_result.location
                print(f"获取到徐州东站坐标: {xzd_loc}")
        
        print(f"调用 maps_driving_by_coordinates(origin={poi_loc}, destination={xzd_loc})")
        driving_result = maps_driving_by_coordinates(
            origin=poi_loc,
            destination=xzd_loc
        )
        
        if driving_result.error:
            print(f"驾车路线规划失败: {driving_result.error}")
            print("验证步骤4: 未通过")
        else:
            if driving_result.total_duration_seconds is not None:
                duration = driving_result.total_duration_seconds
                if duration <= max_driving_duration_seconds:
                    print(f"验证步骤4: 通过 - 驾车时间 {duration}秒 <= {max_driving_duration_seconds}秒")
                    passed_count += 1
                else:
                    print(f"验证步骤4: 未通过 - 驾车时间 {duration}秒 > {max_driving_duration_seconds}秒")
            else:
                print("验证步骤4: 未通过 - 无法获取驾车时间")
    
    # 验证步骤5: 200米内有地铁站
    print("\n验证步骤5: 200米内有地铁站")
    if not poi_loc:
        print("验证步骤5: 未通过 - 无法获取POI坐标，无法搜索地铁站")
    else:
        print(f"调用 maps_around_search(location={poi_loc}, radius=\"{metro_search_radius}\", keywords=\"{metro_search_keywords}\")")
        metro_around_result = maps_around_search(
            location=poi_loc,
            radius=metro_search_radius,
            keywords=metro_search_keywords
        )
        
        if metro_around_result.error:
            print(f"周边搜索失败: {metro_around_result.error}")
            print("验证步骤5: 未通过")
        else:
            pois = metro_around_result.pois or []
            if len(pois) >= 1:
                print(f"验证步骤5: 通过 - 找到 {len(pois)} 个地铁站")
                passed_count += 1
            else:
                print(f"验证步骤5: 未通过 - 未找到地铁站（返回POI数量: {len(pois)}）")
    
    # 输出最终结果
    print(f"\n验证完成: 通过 {passed_count}/{total_count} 项验证")
    if passed_count == total_count:
        print("最终验证结果: True (完全满足所有验证条件)")
        return True
    else:
        print("最终验证结果: False (部分满足或不满足验证条件)")
        return False


def main():
    result = verify_poi()
    print(f"\n函数返回值: {result}")


if __name__ == "__main__":
    main()

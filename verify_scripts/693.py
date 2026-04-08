"""
输入：B0G39COE6S
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边覆盖验证：调用 maps_around_search(location="125.285952,43.867332", radius="3500", keywords="购物中心")，验证返包含目标poi_id=B0G39COE6S。
2) POI属性验证：调用 maps_search_detail(id="B0G39COE6S") 获取location与biz_ext.rating，验证 rating>=4.8。
3) 步行时间验证：用 maps_walking_by_coordinates(origin="125.285952,43.867332", destination="125.292631,43.866919")，验证 total_duration_seconds<=960（16分钟）。
4) 到长春站驾车时间验证：调用 maps_text_search(keywords="长春站", city="长春") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取长春站location；再用 maps_driving_by_coordinates(origin="125.292631,43.866919", destination=长春站location)，验证 total_duration_seconds<=720（12分钟）。
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
    target_poi_id: str = "B0G39COE6S",
    user_location: str = "125.285952,43.867332",
    around_search_radius: str = "3500",
    around_search_keywords: str = "购物中心",
    min_rating: float = 4.8,
    max_walking_duration_seconds: int = 960,
    poi_location: str = "125.292631,43.866919",
    station_address: str = "长春站",
    station_city: str = "长春",
    station_location: str = "125.321938,43.907379",
    max_driving_duration_seconds: int = 720
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        min_rating: 最低评分要求
        max_walking_duration_seconds: 最大步行时间（秒）
        poi_location: POI位置坐标
        station_address: 车站地址
        station_city: 车站所在城市
        station_location: 车站位置坐标（如果maps_text_search+maps_search_detail获取失败则使用此默认值）
        max_driving_duration_seconds: 最大驾车时间（秒）
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 4
    
    # 使用局部变量存储POI location（可能从详情中获取）
    actual_poi_location = poi_location
    
    # 验证步骤1: 周边覆盖验证
    print("验证步骤1: 周边覆盖验证")
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
    
    # 验证步骤2: POI属性验证
    print("\n验证步骤2: POI属性验证")
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
            print(f"验证步骤2: 未通过 - 无法获取POI评分信息")
        
        # 更新POI location（如果从详情中获取到了）
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"从POI详情获取到location: {actual_poi_location}")
    
    # 验证步骤3: 步行时间验证
    print("\n验证步骤3: 步行时间验证")
    print(f"调用 maps_walking_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=actual_poi_location
    )
    
    if walking_result.error:
        print(f"步行路线规划失败: {walking_result.error}")
        print("验证步骤3: 未通过")
    else:
        if walking_result.total_duration_seconds is not None:
            if walking_result.total_duration_seconds <= max_walking_duration_seconds:
                print(f"验证步骤3: 通过 - 步行时间 {walking_result.total_duration_seconds}秒 <= {max_walking_duration_seconds}秒")
                passed_count += 1
            else:
                print(f"验证步骤3: 未通过 - 步行时间 {walking_result.total_duration_seconds}秒 > {max_walking_duration_seconds}秒")
        else:
            print("验证步骤3: 未通过 - 无法获取步行时间")
    
    # 验证步骤4: 用 maps_text_search + maps_search_detail 获取长春站坐标，到长春站驾车时间验证
    print("\n验证步骤4: 到长春站驾车时间验证")
    print(f"调用 maps_text_search(keywords=\"{station_address}\", city=\"{station_city}\") 获取 poi_id，再 maps_search_detail 获取坐标")
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    station_coord = station_location  # 默认使用提供的坐标
    if text_search_result.error:
        print(f"文本搜索失败: {text_search_result.error}")
        print(f"使用默认坐标: {station_coord}")
    elif not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"未找到长春站POI，使用默认坐标: {station_coord}")
    else:
        first_poi_id = text_search_result.pois[0].id
        detail_result = maps_search_detail(id=first_poi_id)
        if detail_result.error or not detail_result.location:
            print(f"获取详情失败: {detail_result.error or '无location'}")
            print(f"使用默认坐标: {station_coord}")
        else:
            station_coord = detail_result.location
            print(f"获取到长春站坐标: {station_coord}")
    
    print(f"调用 maps_driving_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{station_coord}\")")
    driving_result = maps_driving_by_coordinates(
        origin=actual_poi_location,
        destination=station_coord
    )
    
    if driving_result.error:
        print(f"驾车路线规划失败: {driving_result.error}")
        print("验证步骤4: 未通过")
    else:
        if driving_result.total_duration_seconds is not None:
            if driving_result.total_duration_seconds <= max_driving_duration_seconds:
                print(f"验证步骤4: 通过 - 驾车时间 {driving_result.total_duration_seconds}秒 <= {max_driving_duration_seconds}秒")
                passed_count += 1
            else:
                print(f"验证步骤4: 未通过 - 驾车时间 {driving_result.total_duration_seconds}秒 > {max_driving_duration_seconds}秒")
        else:
            print("验证步骤4: 未通过 - 无法获取驾车时间")
    
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

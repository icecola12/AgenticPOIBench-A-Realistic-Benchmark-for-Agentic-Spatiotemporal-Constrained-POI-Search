"""
修改任务指令：你要找一家附近2公里内的便利店，走路过去最好别超过25分钟。店铺评分要在4.2分及以上。为了等会儿赶去金华站坐车，这家店开车到金华站的时间需要在15分钟以内。这家店附近300米需要有公交站。你说话非常有条理和注重细节
输入：B0FFFXQFHR
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（附近2公里内）：调用maps_around_search(location="119.654117,29.060343", radius="2000", keywords="便利店")，验证返回pois中包含目标poi_id=B0FFFXQFHR。
2) 步行时间不超过25分钟：对目标poi_id调用maps_search_detail("B0FFFXQFHR")获取其location=119.661391,29.063231；再调用maps_walking_by_coordinates(origin="119.654117,29.060343", destination="119.661391,29.063231")，验证total_duration_seconds <= 1500。
3) 评分不低于4.2：调用maps_search_detail("B0FFFXQFHR")，读取biz_ext.rating，验证rating >= 4.2（目标为4.3）。
4) 开车到金华站不超过15分钟：调用 maps_text_search(keywords="金华站", city="金华") 取 poi_id，再 maps_search_detail(id=poi_id) 得到 金华站坐标 location_station；调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 900。
5) 店附近300米需要有公交站：调用maps_around_search(location="119.661391,29.063231", radius="300", keywords="公交站")，验证返回pois数量>0。
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
    maps_driving_by_coordinates ,
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
    target_poi_id: str = "B0FFFXQFHR",
    user_location: str = "119.654117,29.060343",
    around_search_radius: str = "2000",
    around_search_keywords: str = "便利店",
    max_walking_duration_seconds: int = 1500,
    poi_location: str = "119.661391,29.063231",
    min_rating: float = 4.2,
    station_address: str = "金华站",
    station_city: str = "金华",
    station_location: str = "119.635860,29.110764",
    max_driving_duration_seconds: int = 900,
    bus_station_search_radius: str = "300",
    bus_station_search_keywords: str = "公交站"
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    验证步骤：
    1) 距离约束（附近2公里内）：验证目标POI是否在用户附近2公里内的便利店列表中
    2) 步行时间不超过25分钟：验证从用户位置到POI的步行时间<=25分钟
    3) 评分不低于4.2：验证POI评分>=4.2
    4) 开车到金华站不超过15分钟：验证从POI到金华站的驾车时间<=15分钟
    5) 店附近300米需要有公交站：验证POI周围300米内存在公交站
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        max_walking_duration_seconds: 最大步行时间（秒），25分钟=1500秒
        poi_location: POI位置坐标（如果从详情中未获取到可通过此参数传入）
        min_rating: 最低评分要求
        station_address: 车站地址
        station_city: 车站所在城市
        station_location: 车站位置坐标（如果获取失败则使用此默认值）
        max_driving_duration_seconds: 最大驾车时间（秒），15分钟=900秒
        bus_station_search_radius: 公交站搜索半径
        bus_station_search_keywords: 公交站搜索关键词
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 5
    
    # 实际用于后续计算的POI坐标，优先使用POI详情中的location
    actual_poi_location = poi_location
    
    # 验证步骤1: 距离约束（附近2公里内）验证
    print("验证步骤1: 距离约束（附近2公里内）验证")
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
    
    # 验证步骤2: 步行时间不超过25分钟验证
    print("\n验证步骤2: 步行时间不超过25分钟验证")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤2: 未通过")
    else:
        # 更新POI location（如果从详情中获取到了）
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"从POI详情获取到location: {actual_poi_location}")
        
        if not actual_poi_location:
            print("验证步骤2: 未通过 - 无法获取POI坐标，无法规划步行路线")
        else:
            print(f"调用 maps_walking_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
            walking_result = maps_walking_by_coordinates(
                origin=user_location,
                destination=actual_poi_location
            )
            
            if walking_result.error:
                print(f"步行路线规划失败: {walking_result.error}")
                print("验证步骤2: 未通过")
            else:
                if walking_result.total_duration_seconds is not None:
                    duration = walking_result.total_duration_seconds
                    if duration <= max_walking_duration_seconds:
                        print(f"验证步骤2: 通过 - 步行时间 {duration}秒 <= {max_walking_duration_seconds}秒")
                        passed_count += 1
                    else:
                        print(f"验证步骤2: 未通过 - 步行时间 {duration}秒 > {max_walking_duration_seconds}秒")
                else:
                    print("验证步骤2: 未通过 - 无法获取步行时间")
    
    # 验证步骤3: 评分不低于4.2验证
    print("\n验证步骤3: 评分不低于4.2验证")
    if detail_result.error:
        print("验证步骤3: 未通过 - POI详情查询失败，无法获取评分信息")
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
                print(f"验证步骤3: 通过 - POI评分 {rating} >= {min_rating}")
                passed_count += 1
            else:
                print(f"验证步骤3: 未通过 - POI评分 {rating} < {min_rating}")
        else:
            print("验证步骤3: 未通过 - 无法获取POI评分信息")
    
    # 验证步骤4: 开车到金华站不超过15分钟验证
    print("\n验证步骤4: 开车到金华站不超过15分钟验证")
    if not actual_poi_location:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        station_text_result = maps_text_search(keywords=station_address, city=station_city)
        station_coord = station_location  # 默认使用提供的坐标
        if station_text_result.error:
            print(f"地理编码失败: {station_text_result.error}")
            print(f"使用默认坐标: {station_coord}")
        else:
            if station_text_result.pois and len(station_text_result.pois) > 0:
                first_poi_id = station_text_result.pois[0].id
                station_detail_result = maps_search_detail(id=first_poi_id)
                if station_detail_result.error:
                    print(f"❌ 获取坐标失败: {station_detail_result.error}")
                    return False
                if not station_detail_result.location:
                    print("❌ 未获取到坐标")
                    return False
                station_coord = station_detail_result.location
                print(f"获取到金华站坐标: {station_coord}")
            else:
                print(f"未找到金华站坐标，使用默认坐标: {station_coord}")
        
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
                duration = driving_result.total_duration_seconds
                if duration <= max_driving_duration_seconds:
                    print(f"验证步骤4: 通过 - 驾车时间 {duration}秒 <= {max_driving_duration_seconds}秒")
                    passed_count += 1
                else:
                    print(f"验证步骤4: 未通过 - 驾车时间 {duration}秒 > {max_driving_duration_seconds}秒")
            else:
                print("验证步骤4: 未通过 - 无法获取驾车时间")
    
    # 验证步骤5: 店附近300米需要有公交站验证
    print("\n验证步骤5: 店附近300米需要有公交站验证")
    if not actual_poi_location:
        print("验证步骤5: 未通过 - 无法获取POI坐标，无法搜索公交站")
    else:
        print(f"调用 maps_around_search(location=\"{actual_poi_location}\", radius=\"{bus_station_search_radius}\", keywords=\"{bus_station_search_keywords}\")")
        bus_station_result = maps_around_search(
            location=actual_poi_location,
            radius=bus_station_search_radius,
            keywords=bus_station_search_keywords
        )
        
        if bus_station_result.error:
            print(f"公交站搜索失败: {bus_station_result.error}")
            print("验证步骤5: 未通过")
        else:
            if bus_station_result.pois and len(bus_station_result.pois) > 0:
                print(f"验证步骤5: 通过 - 在POI周围{bus_station_search_radius}米内找到 {len(bus_station_result.pois)} 个公交站")
                passed_count += 1
            else:
                print(f"验证步骤5: 未通过 - 在POI周围{bus_station_search_radius}米内未找到公交站")
    
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

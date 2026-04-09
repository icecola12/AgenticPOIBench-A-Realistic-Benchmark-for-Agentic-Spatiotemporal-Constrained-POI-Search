"""
修改任务指令：你要找附近2500米内的银行网点。你打算骑车去取一份比较急的材料，所以从你这里骑行过去不要超过12分钟。到了之后你还得马上转去南昌站赶车，因此从这个银行开车到南昌站不要超过20分钟。另外，你希望这个银行离最近的地铁站步行不超过10分钟，方便同事也能过来汇合。你健谈外向，乐观，乐于合作。
输入：B0FFGW1R9B
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束：调用 maps_around_search(location='115.921282,28.689479', radius='2500', keywords='银行')，验证返回pois中包含目标poi_id=B0FFGW1R9B。
2) POI类型约束（排除ATM/自助银行）：调用 maps_search_detail(id='B0FFGW1R9B')，检查 name 字段不包含“ATM”“自助银行”“24小时自助银行”等关键词，且名称语义为银行支行/网点（如“XX银行(XX支行)”）。若包含上述排除词则不通过。
3) 骑行时间约束：从 maps_search_detail 获取目标POI的location，调用 maps_bicycling_by_coordinates(origin='115.921282,28.689479', destination=poi.location)，验证 total_duration_seconds <= 720。
4) 到火车站驾车时间约束：调用 maps_text_search(keywords='南昌站', city='南昌') 取 poi_id，再 maps_search_detail(id=poi_id) 获取 南昌站坐标 station_loc；再调用 maps_driving_by_coordinates(origin=poi.location, destination=station_loc)，验证 total_duration_seconds <= 1200。
5) 地铁站步行时间约束：以目标POI坐标为中心调用 maps_around_search(location=poi.location, radius='1200', keywords='地铁站')，取返回pois中任意一个地铁站poi的location=metro_loc；调用 maps_walking_by_coordinates(origin=poi.location, destination=metro_loc)，验证 total_duration_seconds <= 600。
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
    target_poi_id: str = "B0FFGW1R9B",
    user_location: str = "115.921282,28.689479",
    around_search_radius: str = "2500",
    around_search_keywords: str = "银行",
    max_bicycling_duration_seconds: int = 720,
    station_address: str = "南昌站",
    station_city: str = "南昌",
    max_driving_duration_seconds: int = 1200,
    metro_search_radius: str = "1200",
    metro_search_keywords: str = "地铁站",
    max_walking_duration_seconds: int = 600
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    验证步骤：
    1) 距离约束：验证目标POI是否在用户附近2500米内的银行列表中
    2) POI类型约束（排除ATM/自助银行）：验证POI名称不包含排除关键词
    3) 骑行时间约束：验证从用户位置到POI的骑行时间<=12分钟
    4) 到火车站驾车时间约束：验证从POI到南昌站的驾车时间<=20分钟
    5) 地铁站步行时间约束：验证从POI到最近地铁站的步行时间<=10分钟
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        max_bicycling_duration_seconds: 最大骑行时间（秒），12分钟=720秒
        station_address: 车站地址
        station_city: 车站所在城市
        max_driving_duration_seconds: 最大驾车时间（秒），20分钟=1200秒
        metro_search_radius: 地铁站搜索半径
        metro_search_keywords: 地铁站搜索关键词
        max_walking_duration_seconds: 最大步行时间（秒），10分钟=600秒
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 5
    
    # 实际用于后续计算的POI坐标，从POI详情中获取
    actual_poi_location = None
    
    # 验证步骤1: 距离约束验证
    print("验证步骤1: 距离约束验证")
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
    
    # 验证步骤2: POI类型约束（排除ATM/自助银行）验证
    print("\n验证步骤2: POI类型约束（排除ATM/自助银行）验证")
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
        
        # 检查名称是否包含排除关键词
        exclude_keywords = ["ATM", "自助银行", "24小时自助银行"]
        name_passed = False
        
        if detail_result.name:
            poi_name = detail_result.name
            print(f"POI名称: {poi_name}")
            
            # 检查是否包含排除关键词
            contains_exclude_keyword = False
            for keyword in exclude_keywords:
                if keyword in poi_name:
                    contains_exclude_keyword = True
                    print(f"验证步骤2: 未通过 - POI名称包含排除关键词: {keyword}")
                    break
            
            if not contains_exclude_keyword:
                # 检查名称语义是否为银行支行/网点（包含"银行"且可能包含"支行"或"网点"等）
                if "银行" in poi_name:
                    print(f"验证步骤2: 通过 - POI名称 {poi_name} 符合银行支行/网点要求，且不包含排除关键词")
                    name_passed = True
                else:
                    print(f"验证步骤2: 未通过 - POI名称 {poi_name} 不包含\"银行\"关键词")
        else:
            print("验证步骤2: 未通过 - 无法获取POI名称信息")
        
        if name_passed:
            passed_count += 1
    
    # 验证步骤3: 骑行时间约束验证
    print("\n验证步骤3: 骑行时间约束验证")
    if not actual_poi_location:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法规划骑行路线")
    else:
        print(f"调用 maps_bicycling_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
        bicycling_result = maps_bicycling_by_coordinates(
            origin=user_location,
            destination=actual_poi_location
        )
        
        if bicycling_result.error:
            print(f"骑行路线规划失败: {bicycling_result.error}")
            print("验证步骤3: 未通过")
        else:
            if bicycling_result.total_duration_seconds is not None:
                duration = bicycling_result.total_duration_seconds
                if duration <= max_bicycling_duration_seconds:
                    print(f"验证步骤3: 通过 - 骑行时间 {duration}秒 <= {max_bicycling_duration_seconds}秒")
                    passed_count += 1
                else:
                    print(f"验证步骤3: 未通过 - 骑行时间 {duration}秒 > {max_bicycling_duration_seconds}秒")
            else:
                print("验证步骤3: 未通过 - 无法获取骑行时间")
    
    # 验证步骤4: 到火车站驾车时间约束验证
    print("\n验证步骤4: 到火车站驾车时间约束验证")
    if not actual_poi_location:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        station_text_result = maps_text_search(keywords=station_address, city=station_city)
        if station_text_result.error:
            print(f"地理编码失败: {station_text_result.error}")
            print("验证步骤4: 未通过")
        else:
            if not station_text_result.pois:
                print("未找到南昌站的坐标")
                print("验证步骤4: 未通过")
            else:
                first_poi_id = station_text_result.pois[0].id
                station_detail_result = maps_search_detail(id=first_poi_id)
                if station_detail_result.error:
                    print(f"❌ 获取坐标失败: {station_detail_result.error}")
                    return False
                if not station_detail_result.location:
                    print("❌ 未获取到坐标")
                    return False
                station_location = station_detail_result.location
                print(f"获取到南昌站坐标: {station_location}")
                print(f"调用 maps_driving_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{station_location}\")")
                driving_result = maps_driving_by_coordinates(
                    origin=actual_poi_location,
                    destination=station_location
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
    
    # 验证步骤5: 地铁站步行时间约束验证
    print("\n验证步骤5: 地铁站步行时间约束验证")
    if not actual_poi_location:
        print("验证步骤5: 未通过 - 无法获取POI坐标，无法搜索地铁站")
    else:
        print(f"调用 maps_around_search(location=\"{actual_poi_location}\", radius=\"{metro_search_radius}\", keywords=\"{metro_search_keywords}\")")
        metro_result = maps_around_search(
            location=actual_poi_location,
            radius=metro_search_radius,
            keywords=metro_search_keywords
        )
        
        if metro_result.error:
            print(f"地铁站搜索失败: {metro_result.error}")
            print("验证步骤5: 未通过")
        else:
            if not metro_result.pois or len(metro_result.pois) == 0:
                print("验证步骤5: 未通过 - 在POI周围未找到地铁站")
            else:
                # 取第一个地铁站的location
                metro_location = metro_result.pois[0].location
                print(f"获取到地铁站坐标: {metro_location}")
                print(f"调用 maps_walking_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{metro_location}\")")
                walking_result = maps_walking_by_coordinates(
                    origin=actual_poi_location,
                    destination=metro_location
                )
                
                if walking_result.error:
                    print(f"步行路线规划失败: {walking_result.error}")
                    print("验证步骤5: 未通过")
                else:
                    if walking_result.total_duration_seconds is not None:
                        duration = walking_result.total_duration_seconds
                        if duration <= max_walking_duration_seconds:
                            print(f"验证步骤5: 通过 - 步行时间 {duration}秒 <= {max_walking_duration_seconds}秒")
                            passed_count += 1
                        else:
                            print(f"验证步骤5: 未通过 - 步行时间 {duration}秒 > {max_walking_duration_seconds}秒")
                    else:
                        print("验证步骤5: 未通过 - 无法获取步行时间")
    
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

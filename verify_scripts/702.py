"""
修改任务指令：你想在附近1.5km内找一家药店，步行过去不超过12分钟。你接下来要开车去自贡北站，所以从药店开车到自贡北站也得控制在8分钟内。为了避免走回头路，你选的药店需要离“滨江路老百货大楼(公交站)”的直线距离至少300米远。另外你希望药店附近500米内就有公交站，方便同行的人改坐公交。你没有耐心，说话直接
输入：B0KBDZI0G6
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边候选验证：调用 maps_around_search(location="104.768542,29.34503", radius="1500", keywords="药店")，验证返回pois中包含 target_poi_id=B0KBDZI0G6。
2) POI类型核验：对 target_poi_id 调用 maps_search_detail(id="B0KBDZI0G6")，确认其名称/类别为药店（名称为“大参林(高坪地路店)”。
3) 步行时间约束：调用 maps_walking_by_coordinates(origin="104.768542,29.345030", destination="104.765531,29.348432")，验证 total_duration_seconds<=720（实际667秒）。
4) 驾车到自贡北站时间约束：先调用 maps_text_search(keywords="自贡北站", city="自贡", citylimit="true") 获取车站poi_id=B032D00DHT；再 maps_search_detail(id="B032D00DHT") 获取location="104.791377,29.355921"；最后调用 maps_driving_by_coordinates(origin="104.765531,29.348432", destination="104.791377,29.355921")，验证 total_duration_seconds<=480（实际325秒）。
5) 排除半径约束：调用 maps_text_search(keywords="滨江路老百货大楼(公交站)", city="自贡", citylimit="true") 获取poi_id=BV11139627；再 maps_search_detail(id="BV11139627") 得到location="104.768646,29.348103"；调用 maps_distance(origins="104.765531,29.348432", destination="104.768646,29.348103")，验证distance_meters>=300（实际304米）。
6) 附近公交站约束：调用 maps_around_search(location="104.765531,29.348432", radius="500", keywords="公交站")，验证返回pois数量>0（例如包含“十字口(公交站)”等）。
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
    target_poi_id: str = "B0KBDZI0G6",
    user_location: str = "104.768542,29.34503",
    around_search_radius: str = "1500",
    around_search_keywords: str = "药店",
    poi_location: str = "104.765531,29.348432",
    max_walking_duration_seconds: int = 720,
    station_keywords: str = "自贡北站",
    station_city: str = "自贡",
    station_citylimit: str = "true",
    station_poi_id: str = "B032D00DHT",
    station_location: str = "104.791377,29.355921",
    max_driving_duration_seconds: int = 480,
    exclude_bus_station_keywords: str = "滨江路老百货大楼(公交站)",
    exclude_bus_station_city: str = "自贡",
    exclude_bus_station_citylimit: str = "true",
    exclude_bus_station_poi_id: str = "BV11139627",
    exclude_bus_station_location: str = "104.768646,29.348103",
    min_distance_to_exclude_meters: int = 300,
    bus_station_search_radius: str = "500",
    bus_station_search_keywords: str = "公交站"
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    验证步骤：
    1) 周边候选验证：验证目标POI是否在用户附近1.5km内的药店列表中
    2) POI类型核验：验证POI名称/类别为药店
    3) 步行时间约束：验证从用户位置到POI的步行时间<=12分钟
    4) 驾车到自贡北站时间约束：验证从POI到自贡北站的驾车时间<=8分钟
    5) 排除半径约束：验证POI到"滨江路老百货大楼(公交站)"的直线距离>=300米
    6) 附近公交站约束：验证POI周围500米内存在公交站
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        poi_location: POI位置坐标（如果从详情中未获取到可通过此参数传入）
        max_walking_duration_seconds: 最大步行时间（秒），12分钟=720秒
        station_keywords: 车站搜索关键词
        station_city: 车站所在城市
        station_citylimit: 车站搜索城市限制
        station_poi_id: 车站POI ID（如果maps_text_search获取失败则使用此默认值）
        station_location: 车站位置坐标（如果maps_search_detail获取失败则使用此默认值）
        max_driving_duration_seconds: 最大驾车时间（秒），8分钟=480秒
        exclude_bus_station_keywords: 排除公交站搜索关键词
        exclude_bus_station_city: 排除公交站所在城市
        exclude_bus_station_citylimit: 排除公交站搜索城市限制
        exclude_bus_station_poi_id: 排除公交站POI ID（如果maps_text_search获取失败则使用此默认值）
        exclude_bus_station_location: 排除公交站位置坐标（如果maps_search_detail获取失败则使用此默认值）
        min_distance_to_exclude_meters: 到排除公交站的最小直线距离（米）
        bus_station_search_radius: 公交站搜索半径
        bus_station_search_keywords: 公交站搜索关键词
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 6
    
    # 实际用于后续计算的POI坐标，优先使用POI详情中的location
    actual_poi_location = poi_location
    
    # 验证步骤1: 周边候选验证
    print("验证步骤1: 周边候选验证")
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
    
    # 验证步骤2: POI类型核验
    print("\n验证步骤2: POI类型核验")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤2: 未通过")
    else:
        # 检查名称是否包含"药店"或"大参林"
        name_passed = False
        if detail_result.name:
            poi_name = detail_result.name
            print(f"POI名称: {poi_name}")
            # 验证名称是否为"大参林(高坪地路店)"或包含"药店"关键词
            if "大参林" in poi_name or "药店" in poi_name:
                print(f"验证步骤2: 通过 - POI名称 {poi_name} 符合药店要求")
                name_passed = True
            else:
                print(f"验证步骤2: 未通过 - POI名称 {poi_name} 不符合药店要求")
        else:
            print("验证步骤2: 未通过 - 无法获取POI名称信息")
        
        # 更新POI location（如果从详情中获取到了）
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"从POI详情获取到location: {actual_poi_location}")
        
        if name_passed:
            passed_count += 1
    
    # 验证步骤3: 步行时间约束
    print("\n验证步骤3: 步行时间约束")
    if not actual_poi_location:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法规划步行路线")
    else:
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
                duration = walking_result.total_duration_seconds
                if duration <= max_walking_duration_seconds:
                    print(f"验证步骤3: 通过 - 步行时间 {duration}秒 <= {max_walking_duration_seconds}秒")
                    passed_count += 1
                else:
                    print(f"验证步骤3: 未通过 - 步行时间 {duration}秒 > {max_walking_duration_seconds}秒")
            else:
                print("验证步骤3: 未通过 - 无法获取步行时间")
    
    # 验证步骤4: 驾车到自贡北站时间约束
    print("\n验证步骤4: 驾车到自贡北站时间约束")
    if not actual_poi_location:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        # 步骤4a: 获取自贡北站坐标
        print(f"调用 maps_text_search(keywords=\"{station_keywords}\", city=\"{station_city}\", citylimit=\"{station_citylimit}\")")
        station_search_result = maps_text_search(
            keywords=station_keywords,
            city=station_city,
            citylimit=station_citylimit
        )
        
        station_coord = station_location  # 默认使用提供的坐标
        if station_search_result.error:
            print(f"文本搜索失败: {station_search_result.error}")
            print(f"使用默认坐标: {station_coord}")
        else:
            station_id = None
            if station_search_result.pois:
                # 查找期望的车站POI ID
                for poi in station_search_result.pois:
                    if poi.id == station_poi_id:
                        station_id = poi.id
                        break
                
                # 如果没找到期望的ID，使用第一个结果
                if not station_id and len(station_search_result.pois) > 0:
                    station_id = station_search_result.pois[0].id
                    print(f"未找到期望的车站ID {station_poi_id}，使用搜索结果中的第一个POI ID: {station_id}")
            
            if station_id:
                print(f"获取到车站POI ID: {station_id}")
                print(f"调用 maps_search_detail(id=\"{station_id}\")")
                station_detail_result = maps_search_detail(id=station_id)
                
                if station_detail_result.error:
                    print(f"车站详情查询失败: {station_detail_result.error}")
                    print(f"使用默认坐标: {station_coord}")
                else:
                    if station_detail_result.location:
                        station_coord = station_detail_result.location
                        print(f"获取到车站坐标: {station_coord}")
                    else:
                        print(f"未找到车站坐标，使用默认坐标: {station_coord}")
            else:
                print(f"未找到车站POI，使用默认坐标: {station_coord}")
        
        # 步骤4b: 计算驾车时间
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
    
    # 验证步骤5: 排除半径约束
    print("\n验证步骤5: 排除半径约束")
    if not actual_poi_location:
        print("验证步骤5: 未通过 - 无法获取POI坐标，无法计算距离")
    else:
        # 步骤5a: 获取排除公交站坐标
        print(f"调用 maps_text_search(keywords=\"{exclude_bus_station_keywords}\", city=\"{exclude_bus_station_city}\", citylimit=\"{exclude_bus_station_citylimit}\")")
        exclude_search_result = maps_text_search(
            keywords=exclude_bus_station_keywords,
            city=exclude_bus_station_city,
            citylimit=exclude_bus_station_citylimit
        )
        
        exclude_coord = exclude_bus_station_location  # 默认使用提供的坐标
        if exclude_search_result.error:
            print(f"文本搜索失败: {exclude_search_result.error}")
            print(f"使用默认坐标: {exclude_coord}")
        else:
            exclude_id = None
            if exclude_search_result.pois:
                # 查找期望的公交站POI ID
                for poi in exclude_search_result.pois:
                    if poi.id == exclude_bus_station_poi_id:
                        exclude_id = poi.id
                        break
                
                # 如果没找到期望的ID，使用第一个结果
                if not exclude_id and len(exclude_search_result.pois) > 0:
                    exclude_id = exclude_search_result.pois[0].id
                    print(f"未找到期望的公交站ID {exclude_bus_station_poi_id}，使用搜索结果中的第一个POI ID: {exclude_id}")
            
            if exclude_id:
                print(f"获取到排除公交站POI ID: {exclude_id}")
                print(f"调用 maps_search_detail(id=\"{exclude_id}\")")
                exclude_detail_result = maps_search_detail(id=exclude_id)
                
                if exclude_detail_result.error:
                    print(f"公交站详情查询失败: {exclude_detail_result.error}")
                    print(f"使用默认坐标: {exclude_coord}")
                else:
                    if exclude_detail_result.location:
                        exclude_coord = exclude_detail_result.location
                        print(f"获取到排除公交站坐标: {exclude_coord}")
                    else:
                        print(f"未找到排除公交站坐标，使用默认坐标: {exclude_coord}")
            else:
                print(f"未找到排除公交站POI，使用默认坐标: {exclude_coord}")
        
        # 步骤5b: 计算直线距离
        print(f"调用 maps_distance(origins=\"{actual_poi_location}\", destination=\"{exclude_coord}\")")
        distance_result = maps_distance(
            origins=actual_poi_location,
            destination=exclude_coord
        )
        
        if distance_result.error:
            print(f"距离计算失败: {distance_result.error}")
            print("验证步骤5: 未通过")
        else:
            if distance_result.results and len(distance_result.results) > 0:
                distance_meters = distance_result.results[0].distance_meters
                if distance_meters >= min_distance_to_exclude_meters:
                    print(f"验证步骤5: 通过 - 与排除公交站的直线距离 {distance_meters}米 >= {min_distance_to_exclude_meters}米")
                    passed_count += 1
                else:
                    print(f"验证步骤5: 未通过 - 与排除公交站的直线距离 {distance_meters}米 < {min_distance_to_exclude_meters}米")
            else:
                print("验证步骤5: 未通过 - 未获取到距离结果")
    
    # 验证步骤6: 附近公交站约束
    print("\n验证步骤6: 附近公交站约束")
    if not actual_poi_location:
        print("验证步骤6: 未通过 - 无法获取POI坐标，无法搜索公交站")
    else:
        print(f"调用 maps_around_search(location=\"{actual_poi_location}\", radius=\"{bus_station_search_radius}\", keywords=\"{bus_station_search_keywords}\")")
        bus_station_result = maps_around_search(
            location=actual_poi_location,
            radius=bus_station_search_radius,
            keywords=bus_station_search_keywords
        )
        
        if bus_station_result.error:
            print(f"公交站搜索失败: {bus_station_result.error}")
            print("验证步骤6: 未通过")
        else:
            if bus_station_result.pois and len(bus_station_result.pois) > 0:
                print(f"验证步骤6: 通过 - 在POI周围{bus_station_search_radius}米内找到 {len(bus_station_result.pois)} 个公交站")
                passed_count += 1
            else:
                print(f"验证步骤6: 未通过 - 在POI周围{bus_station_search_radius}米内未找到公交站")
    
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

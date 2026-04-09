"""
修改任务指令：你想在附近3000米内找一家网吧，评分至少4.7分，人均消费不超过30元。网吧不能离咸宁市政府500米以内。你从家开车去网吧的路线上，至少存在一个途径点满足离咸宁购物公园800米以内的点。网吧附近1000米内得有一个公交站，步行过去不能超过10分钟。另外，你朋友从咸宁市政府出发，先到网吧接你，然后你们一起去咸宁火车站，整个行程时间不能超过40分钟。从你家到网吧的开车距离也不能超过5公里。你健忘，且沟通时会随机出现拼写错误。
输入：B0FFFGYLLA
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('114.348284,29.822031', '网吧', 3000)，验证目标网吧（巨星网咖(潜山路店)）在结果列表中
2. 调用maps_search_detail('B0FFFGYLLA')获取详细信息，验证biz_ext.rating≥4.7，biz_ext.cost≤30元（实际为22.00元）
3. 调用maps_distance('114.322601,29.841350', '114.318802,29.829002')计算网吧到咸宁市政府的直线距离，验证>500米（实际约1422米）
4. 调用maps_driving_by_coordinates('114.348284,29.822031', '114.318802,29.829002')获取驾车路线steps，提取每个步骤的from_coordinates/to_coordinates，对每个途径点调用maps_distance计算到咸宁购物公园('114.333527,29.826128')的直线距离，验证至少有一个距离<800米（例如步骤点114.325882,29.827237到购物公园约748米）
5. 调用maps_around_search('114.318802,29.829002', '公交站', 1000)获取附近公交站列表，遍历每个公交站，调用maps_walking_by_coordinates计算网吧到该公交站的步行时间，验证至少存在一个公交站步行时间≤600秒（实际约560秒）
6. 调用maps_driving_by_coordinates('114.322601,29.841350', '114.318802,29.829002')获取市政府到网吧的驾车时间t1，调用maps_driving_by_coordinates('114.318802,29.829002', '114.288539,29.879450')获取网吧到火车站的驾车时间t2，验证(t1+t2)≤2400秒（实际约970秒）
7. 调用maps_driving_by_coordinates('114.348284,29.822031', '114.318802,29.829002')获取用户家到网吧的驾车距离，验证total_distance_meters≤5000米（实际约3066米）
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
    maps_geo,
    maps_walking_by_coordinates,
    maps_around_search,
    maps_text_search,
    maps_bicycling_by_coordinates
)

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(target_poi_id: str = 'B0FFFGYLLA') -> bool:
    """
    验证POI是否符合所有要求

    Args:
        target_poi_id: 目标POI的ID，默认值为'B0FFFGYLLA'

    Returns:
        bool: 验证通过返回True，否则返回False
    """
    # 验证步骤计数器
    steps_passed = []
    steps_failed = []

    try:
        # 步骤1: 验证目标网吧在周边搜索结果中
        print("验证步骤1: 验证目标网吧在周边搜索结果中")
        user_location = '114.348284,29.822031'  # 用户位置坐标（固定）
        around_search_result = maps_around_search(user_location, '3000', '网吧')
        if around_search_result.error or not around_search_result.pois:
            print(f"步骤1失败: 周边搜索失败 - {around_search_result.error}")
            steps_failed.append(1)
            return False

        # 检查目标POI是否在搜索结果中
        target_found = False
        for poi in around_search_result.pois:
            if poi.id == target_poi_id:
                target_found = True
                break

        if target_found:
            print("步骤1通过: 目标网吧在周边搜索结果中")
            steps_passed.append(1)
        else:
            print("步骤1失败: 目标网吧不在周边搜索结果中")
            steps_failed.append(1)
            return False

        # 步骤2: 获取POI详细信息并验证评分和人均消费
        print("验证步骤2: 获取POI详细信息并验证评分和人均消费")
        poi_detail = maps_search_detail(target_poi_id)
        if poi_detail.error or not poi_detail.location:
            print(f"步骤2失败: 无法获取POI详细信息 - {poi_detail.error}")
            steps_failed.append(2)
            return False

        # 获取网吧坐标（用于后续计算）
        internet_cafe_location = poi_detail.location
        print(f"网吧坐标: {internet_cafe_location}")

        # 验证评分 ≥ 4.7
        if not poi_detail.biz_ext or 'rating' not in poi_detail.biz_ext:
            print("步骤2失败: 无法获取评分信息")
            steps_failed.append(2)
            return False

        rating = float(poi_detail.biz_ext['rating'])
        if rating < 4.7:
            print(f"步骤2失败: 评分 {rating} < 4.7")
            steps_failed.append(2)
            return False

        # 验证人均消费 ≤ 30元
        if not poi_detail.biz_ext or 'cost' not in poi_detail.biz_ext:
            print("步骤2失败: 无法获取人均消费信息")
            steps_failed.append(2)
            return False

        cost = float(poi_detail.biz_ext['cost'])
        if cost > 30:
            print(f"步骤2失败: 人均消费 {cost}元 > 30元")
            steps_failed.append(2)
            return False

        print(f"步骤2通过: 评分 {rating} ≥ 4.7，人均消费 {cost}元 ≤ 30元")
        steps_passed.append(2)

        # 步骤3: 验证到咸宁市政府的距离 > 500米
        print("验证步骤3: 验证到咸宁市政府的距离")

        # 获取咸宁市政府坐标
        government_search = maps_text_search('咸宁市政府', '咸宁')
        if government_search.error or not government_search.pois:
            print(f"步骤3失败: 无法搜索咸宁市政府 - {government_search.error}")
            steps_failed.append(3)
            return False

        government_detail = maps_search_detail(government_search.pois[0].id)
        if government_detail.error or not government_detail.location:
            print(f"步骤3失败: 无法获取咸宁市政府详细信息 - {government_detail.error}")
            steps_failed.append(3)
            return False

        government_location = government_detail.location

        distance_result = maps_distance(internet_cafe_location, government_location)
        if distance_result.error or not distance_result.results:
            print(f"步骤3失败: 无法计算距离 - {distance_result.error}")
            steps_failed.append(3)
            return False

        distance = distance_result.results[0].distance_meters
        if distance > 500:
            print(f"步骤3通过: 距离咸宁市政府 {distance}米 > 500米")
            steps_passed.append(3)
        else:
            print(f"步骤3失败: 距离咸宁市政府 {distance}米 ≤ 500米")
            steps_failed.append(3)
            return False

        # 步骤4: 验证驾车路线途径点到咸宁购物公园的距离
        print("验证步骤4: 验证驾车路线途径点到咸宁购物公园的距离")

        # 获取咸宁购物公园坐标
        mall_search = maps_text_search('咸宁购物公园', '咸宁')
        if mall_search.error or not mall_search.pois:
            print(f"步骤4失败: 无法搜索咸宁购物公园 - {mall_search.error}")
            steps_failed.append(4)
            return False

        mall_detail = maps_search_detail(mall_search.pois[0].id)
        if mall_detail.error or not mall_detail.location:
            print(f"步骤4失败: 无法获取咸宁购物公园详细信息 - {mall_detail.error}")
            steps_failed.append(4)
            return False

        mall_location = mall_detail.location

        # 获取用户家到网吧的驾车路线
        driving_route = maps_driving_by_coordinates(user_location, internet_cafe_location)
        if driving_route.error or not driving_route.steps:
            print(f"步骤4失败: 无法获取驾车路线 - {driving_route.error}")
            steps_failed.append(4)
            return False

        # 检查是否有途径点距离购物公园 < 800米
        has_nearby_mall = False
        for step in driving_route.steps:
            # 检查from_coordinates和to_coordinates
            waypoints = [step.from_coordinates, step.to_coordinates]
            for waypoint in waypoints:
                if waypoint:
                    distance_to_mall = maps_distance(waypoint, mall_location)
                    if not distance_to_mall.error and distance_to_mall.results:
                        mall_distance = distance_to_mall.results[0].distance_meters
                        if mall_distance < 800:
                            has_nearby_mall = True
                            print(f"步骤4通过: 途径点 {waypoint} 距离咸宁购物公园 {mall_distance}米 < 800米")
                            break
            if has_nearby_mall:
                break

        if has_nearby_mall:
            steps_passed.append(4)
        else:
            print("步骤4失败: 所有途径点距离咸宁购物公园都 ≥ 800米")
            steps_failed.append(4)
            return False

        # 步骤5: 验证附近1000米内有公交站且步行时间 ≤ 600秒
        print("验证步骤5: 验证附近公交站步行时间")

        bus_search = maps_around_search(internet_cafe_location, '1000', '公交站')
        if bus_search.error:
            print(f"步骤5失败: 无法搜索公交站 - {bus_search.error}")
            steps_failed.append(5)
            return False

        bus_stations = bus_search.pois if bus_search.pois else []
        if not bus_stations:
            print("步骤5失败: 附近1000米内没有公交站")
            steps_failed.append(5)
            return False

        # 检查是否有公交站步行时间 ≤ 600秒
        has_nearby_bus = False
        for station in bus_stations:
            if station.location:
                walking_to_bus = maps_walking_by_coordinates(internet_cafe_location, station.location)
                if not walking_to_bus.error and walking_to_bus.total_duration_seconds is not None:
                    duration_seconds = walking_to_bus.total_duration_seconds
                    if duration_seconds <= 600:
                        has_nearby_bus = True
                        print(f"步骤5通过: 公交站 '{station.name}' 步行时间 {duration_seconds}秒 ≤ 600秒")
                        break

        if has_nearby_bus:
            steps_passed.append(5)
        else:
            print("步骤5失败: 所有公交站步行时间都 > 600秒")
            steps_failed.append(5)
            return False

        # 步骤6: 验证市政府到网吧再到火车站的总驾车时间 ≤ 2400秒
        print("验证步骤6: 验证市政府到网吧再到火车站的总驾车时间")

        # 获取咸宁火车站坐标
        station_search = maps_text_search('咸宁火车站', '咸宁')
        if station_search.error or not station_search.pois:
            print(f"步骤6失败: 无法搜索咸宁火车站 - {station_search.error}")
            steps_failed.append(6)
            return False

        station_detail = maps_search_detail(station_search.pois[0].id)
        if station_detail.error or not station_detail.location:
            print(f"步骤6失败: 无法获取咸宁火车站详细信息 - {station_detail.error}")
            steps_failed.append(6)
            return False

        station_location = station_detail.location

        # 计算市政府到网吧的驾车时间
        drive_gov_to_cafe = maps_driving_by_coordinates(government_location, internet_cafe_location)
        if drive_gov_to_cafe.error or drive_gov_to_cafe.total_duration_seconds is None:
            print(f"步骤6失败: 无法计算市政府到网吧驾车时间 - {drive_gov_to_cafe.error}")
            steps_failed.append(6)
            return False

        t1_seconds = drive_gov_to_cafe.total_duration_seconds

        # 计算网吧到火车站的驾车时间
        drive_cafe_to_station = maps_driving_by_coordinates(internet_cafe_location, station_location)
        if drive_cafe_to_station.error or drive_cafe_to_station.total_duration_seconds is None:
            print(f"步骤6失败: 无法计算网吧到火车站驾车时间 - {drive_cafe_to_station.error}")
            steps_failed.append(6)
            return False

        t2_seconds = drive_cafe_to_station.total_duration_seconds

        total_drive_time = t1_seconds + t2_seconds
        if total_drive_time <= 2400:
            print(f"步骤6通过: 总驾车时间 {total_drive_time}秒 ≤ 2400秒")
            steps_passed.append(6)
        else:
            print(f"步骤6失败: 总驾车时间 {total_drive_time}秒 > 2400秒")
            steps_failed.append(6)
            return False

        # 步骤7: 验证用户家到网吧的驾车距离 ≤ 5000米
        print("验证步骤7: 验证用户家到网吧的驾车距离")

        home_to_cafe_drive = maps_driving_by_coordinates(user_location, internet_cafe_location)
        if home_to_cafe_drive.error or home_to_cafe_drive.total_distance_meters is None:
            print(f"步骤7失败: 无法计算用户家到网吧驾车距离 - {home_to_cafe_drive.error}")
            steps_failed.append(7)
            return False

        drive_distance = home_to_cafe_drive.total_distance_meters
        if drive_distance <= 5000:
            print(f"步骤7通过: 驾车距离 {drive_distance}米 ≤ 5000米")
            steps_passed.append(7)
        else:
            print(f"步骤7失败: 驾车距离 {drive_distance}米 > 5000米")
            steps_failed.append(7)
            return False

        # 所有验证都通过
        return True

    except Exception as e:
        print(f"验证过程中发生异常: {e}")
        return False


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")


if __name__ == "__main__":
    main()

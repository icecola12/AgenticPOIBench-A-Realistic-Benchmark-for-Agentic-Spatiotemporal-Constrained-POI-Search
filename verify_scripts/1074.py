"""
修改任务指令：你想在附近1500米内找一家酒吧，评分要4.5以上，人均消费不超过100元，并且营业到深夜（晚上10点以后还营业）。酒吧离亚洲中心广场的直线距离需要大于500米。你步行去酒吧路线上至少要存在一个途径点满足离长宁大厦公交站的直线距离80米以内，而且那个途径点附近150米内要有加油站。酒吧到昌吉亚中商城公交站的直线距离不超过500米。另外，从酒吧开车到昌吉站的时间不能超过30分钟。你害羞且缺乏安全感，说话犹豫，不自信。
输入：B0KK1AUC3S
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('87.299627,44.010477', '酒吧', '1500')验证目标酒吧在1500米范围内
2. 调用maps_search_detail('B0KK1AUC3S')获取酒吧详细信息，验证rating≥4.5、cost≤100元、10点后还营业
3. 调用maps_text_search('亚洲中心广场', '昌吉回族自治州')获取广场poi_id，再调用maps_search_detail获取坐标，最后调用maps_distance计算酒吧到广场的直线距离，验证>500米。
4. 调用maps_walking_by_coordinates('87.299627,44.010477', '87.293350,44.009999')获取步行路线步骤，遍历每个步骤的from_coordinates和to_coordinates，调用maps_distance计算各点与长宁大厦公交站坐标('87.295221,44.011463')的直线距离，验证存在至少一点距离<80米。
5. 针对上述符合条件的途经点坐标，调用maps_around_search(该坐标, '加油站', '150')验证附近150米内存在加油站（中国石油昌吉长宁加油站）。
6. 调用maps_text_search('昌吉亚中商城公交站', '昌吉回族自治州')获取公交站坐标，或直接使用坐标'87.291687,44.014050'，调用maps_distance计算酒吧到该公交站的直线距离，验证≤500米。
7. 调用maps_text_search('昌吉站', '昌吉回族自治州')获取火车站poi_id，再调用maps_search_detail获取坐标，调用maps_driving_by_coordinates计算酒吧到昌吉站的驾车时间，验证总时长≤1800秒（30分钟）。
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
def verify_poi(target_poi_id: str = 'B0KK1AUC3S',
               user_location: str = '87.299627,44.010477',
               asia_center_square_name: str = '亚洲中心广场',
               asia_center_square_city: str = '昌吉回族自治州',
               changning_bus_station_coords: str = '87.295221,44.011463',
               changji_shopping_mall_bus_name: str = '昌吉亚中商城公交站',
               changji_shopping_mall_bus_city: str = '昌吉回族自治州',
               changji_station_name: str = '昌吉站',
               changji_station_city: str = '昌吉回族自治州') -> bool:
    """
    验证POI是否符合所有要求

    Args:
        target_poi_id: 目标POI的ID，默认值为'B0KK1AUC3S'
        user_location: 用户位置坐标，默认值为'87.299627,44.010477'
        asia_center_square_name: 亚洲中心广场名称，默认值为'亚洲中心广场'
        asia_center_square_city: 亚洲中心广场所在城市，默认值为'昌吉回族自治州'
        changning_bus_station_coords: 长宁大厦公交站坐标，默认值为'87.295221,44.011463'
        changji_shopping_mall_bus_name: 昌吉亚中商城公交站名称，默认值为'昌吉亚中商城公交站'
        changji_shopping_mall_bus_city: 昌吉亚中商城公交站所在城市，默认值为'昌吉回族自治州'
        changji_station_name: 昌吉站名称，默认值为'昌吉站'
        changji_station_city: 昌吉站所在城市，默认值为'昌吉回族自治州'

    Returns:
        bool: 验证通过返回True，否则返回False
    """
    # 验证步骤计数器
    steps_passed = []
    steps_failed = []

    try:
        # 步骤1: 验证目标酒吧在1500米范围内
        print("验证步骤1: 验证目标酒吧在1500米范围内")
        around_search_result = maps_around_search(user_location, '1500', '酒吧')
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
            print("步骤1通过: 目标酒吧在1500米范围内")
            steps_passed.append(1)
        else:
            print("步骤1失败: 目标酒吧不在1500米范围内")
            steps_failed.append(1)
            return False

        # 步骤2: 获取酒吧详细信息并验证评分、人均消费、营业时间
        print("验证步骤2: 获取酒吧详细信息并验证评分、人均消费、营业时间")
        poi_detail = maps_search_detail(target_poi_id)
        if poi_detail.error or not poi_detail.location:
            print(f"步骤2失败: 无法获取POI详细信息 - {poi_detail.error}")
            steps_failed.append(2)
            return False

        # 获取酒吧坐标（用于后续计算）
        bar_location = poi_detail.location
        print(f"酒吧坐标: {bar_location}")

        # 验证评分 ≥ 4.5
        if not poi_detail.biz_ext or 'rating' not in poi_detail.biz_ext:
            print("步骤2失败: 无法获取评分信息")
            steps_failed.append(2)
            return False

        rating = float(poi_detail.biz_ext['rating'])
        if rating < 4.5:
            print(f"步骤2失败: 评分 {rating} < 4.5")
            steps_failed.append(2)
            return False

        # 验证人均消费 ≤ 100元
        if not poi_detail.biz_ext or 'cost' not in poi_detail.biz_ext:
            print("步骤2失败: 无法获取人均消费信息")
            steps_failed.append(2)
            return False

        cost = float(poi_detail.biz_ext['cost'])
        if cost > 100:
            print(f"步骤2失败: 人均消费 {cost}元 > 100元")
            steps_failed.append(2)
            return False

        # 验证营业时间（晚上10点以后还营业）
        if not poi_detail.biz_ext or 'open_time' not in poi_detail.biz_ext:
            print("步骤2失败: 无法获取营业时间信息")
            steps_failed.append(2)
            return False

        open_time = poi_detail.biz_ext['open_time']
        if not is_open_until_late(open_time):
            print(f"步骤2失败: 营业时间 '{open_time}' 未达到晚上10点之后")
            steps_failed.append(2)
            return False

        print(f"步骤2通过: 评分 {rating} ≥ 4.5，人均消费 {cost}元 ≤ 100元，营业时间符合要求")
        steps_passed.append(2)

        # 步骤3: 验证到亚洲中心广场的距离 > 500米
        print("验证步骤3: 验证到亚洲中心广场的距离")

        # 获取亚洲中心广场坐标
        square_search = maps_text_search(asia_center_square_name, asia_center_square_city)
        if square_search.error or not square_search.pois:
            print(f"步骤3失败: 无法搜索亚洲中心广场 - {square_search.error}")
            steps_failed.append(3)
            return False

        square_detail = maps_search_detail(square_search.pois[0].id)
        if square_detail.error or not square_detail.location:
            print(f"步骤3失败: 无法获取亚洲中心广场详细信息 - {square_detail.error}")
            steps_failed.append(3)
            return False

        square_location = square_detail.location

        distance_result = maps_distance(bar_location, square_location)
        if distance_result.error or not distance_result.results:
            print(f"步骤3失败: 无法计算距离 - {distance_result.error}")
            steps_failed.append(3)
            return False

        distance = distance_result.results[0].distance_meters
        if distance > 500:
            print(f"步骤3通过: 到亚洲中心广场距离 {distance}米 > 500米")
            steps_passed.append(3)
        else:
            print(f"步骤3失败: 到亚洲中心广场距离 {distance}米 ≤ 500米")
            steps_failed.append(3)
            return False

        # 步骤4: 获取步行路线并验证途径点条件
        print("验证步骤4: 获取步行路线并验证途径点条件")

        walking_route = maps_walking_by_coordinates(user_location, bar_location)
        if walking_route.error or not walking_route.steps:
            print(f"步骤4失败: 无法获取步行路线 - {walking_route.error}")
            steps_failed.append(4)
            return False

        # 检查是否有途径点距离长宁大厦公交站 < 80米
        has_nearby_bus_station = False
        candidate_waypoints = []

        for step in walking_route.steps:
            # 检查from_coordinates和to_coordinates
            waypoints = [step.from_coordinates, step.to_coordinates]
            for waypoint in waypoints:
                if waypoint:
                    distance_to_bus = maps_distance(waypoint, changning_bus_station_coords)
                    if not distance_to_bus.error and distance_to_bus.results:
                        bus_distance = distance_to_bus.results[0].distance_meters
                        if bus_distance < 80:
                            has_nearby_bus_station = True
                            candidate_waypoints.append(waypoint)
                            print(f"步骤4通过: 途径点 {waypoint} 距离长宁大厦公交站 {bus_distance}米 < 80米")
                            break
            if has_nearby_bus_station:
                break

        if not has_nearby_bus_station:
            print("步骤4失败: 所有途径点距离长宁大厦公交站都 ≥ 80米")
            steps_failed.append(4)
            return False

        steps_passed.append(4)

        # 步骤5: 验证途径点附近150米内有加油站
        print("验证步骤5: 验证途径点附近加油站")

        has_gas_station_nearby = False
        for waypoint in candidate_waypoints:
            gas_search = maps_around_search(waypoint, '150', '加油站')
            if not gas_search.error and gas_search.pois:
                has_gas_station_nearby = True
                print(f"步骤5通过: 途径点 {waypoint} 附近150米内有加油站")
                break

        if has_gas_station_nearby:
            steps_passed.append(5)
        else:
            print("步骤5失败: 符合条件的途径点附近150米内都没有加油站")
            steps_failed.append(5)
            return False

        # 步骤6: 验证到昌吉亚中商城公交站的距离 ≤ 500米
        print("验证步骤6: 验证到昌吉亚中商城公交站的距离")

        # 获取昌吉亚中商城公交站坐标
        bus_search = maps_text_search(changji_shopping_mall_bus_name, changji_shopping_mall_bus_city)
        bus_location = None
        if bus_search.error or not bus_search.pois:
            print(f"无法搜索昌吉亚中商城公交站，使用默认坐标: 87.291687,44.014050")
            bus_location = '87.291687,44.014050'
        else:
            bus_detail = maps_search_detail(bus_search.pois[0].id)
            if bus_detail.error or not bus_detail.location:
                print(f"无法获取昌吉亚中商城公交站详细信息，使用默认坐标: 87.291687,44.014050")
                bus_location = '87.291687,44.014050'
            else:
                bus_location = bus_detail.location

        bus_distance_result = maps_distance(bar_location, bus_location)
        if bus_distance_result.error or not bus_distance_result.results:
            print(f"步骤6失败: 无法计算距离 - {bus_distance_result.error}")
            steps_failed.append(6)
            return False

        bus_distance = bus_distance_result.results[0].distance_meters
        if bus_distance <= 500:
            print(f"步骤6通过: 到昌吉亚中商城公交站距离 {bus_distance}米 ≤ 500米")
            steps_passed.append(6)
        else:
            print(f"步骤6失败: 到昌吉亚中商城公交站距离 {bus_distance}米 > 500米")
            steps_failed.append(6)
            return False

        # 步骤7: 验证开车到昌吉站的时间 ≤ 30分钟（1800秒）
        print("验证步骤7: 验证开车到昌吉站的时间")

        # 获取昌吉站坐标
        station_search = maps_text_search(changji_station_name, changji_station_city)
        if station_search.error or not station_search.pois:
            print(f"步骤7失败: 无法搜索昌吉站 - {station_search.error}")
            steps_failed.append(7)
            return False

        station_detail = maps_search_detail(station_search.pois[0].id)
        if station_detail.error or not station_detail.location:
            print(f"步骤7失败: 无法获取昌吉站详细信息 - {station_detail.error}")
            steps_failed.append(7)
            return False

        station_location = station_detail.location

        driving_result = maps_driving_by_coordinates(bar_location, station_location)
        if driving_result.error or driving_result.total_duration_seconds is None:
            print(f"步骤7失败: 无法计算驾车时间 - {driving_result.error}")
            steps_failed.append(7)
            return False

        drive_time_seconds = driving_result.total_duration_seconds
        if drive_time_seconds <= 1800:
            print(f"步骤7通过: 开车到昌吉站时间 {drive_time_seconds}秒 ≤ 1800秒")
            steps_passed.append(7)
        else:
            print(f"步骤7失败: 开车到昌吉站时间 {drive_time_seconds}秒 > 1800秒")
            steps_failed.append(7)
            return False

        # 所有验证都通过
        return True

    except Exception as e:
        print(f"验证过程中发生异常: {e}")
        return False


def is_open_until_late(open_time_str: str) -> bool:
    """
    检查营业时间是否至少到晚上10点之后

    Args:
        open_time_str: 营业时间字符串

    Returns:
        bool: 如果营业时间至少到晚上10点之后返回True，否则返回False
    """
    import re

    if not open_time_str:
        return False

    # 处理全天营业的情况
    if '24' in open_time_str.lower() or '全天' in open_time_str or '通宵' in open_time_str:
        return True

    # 使用正则表达式提取时间范围
    # 匹配类似 "08:30-22:00" 或 "08:30-次日02:00" 的格式
    time_ranges = re.findall(r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})', open_time_str)

    if not time_ranges:
        # 如果没找到标准格式，尝试其他格式
        # 处理类似 "22:00" 这样的单时间点
        single_times = re.findall(r'(\d{1,2}:\d{2})', open_time_str)
        if single_times:
            for time_str in single_times:
                hour, minute = map(int, time_str.split(':'))
                if hour >= 22:  # 22:00或之后
                    return True
        return False

    # 检查每个时间范围
    for start_time, end_time in time_ranges:
        try:
            # 解析开始和结束时间
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))

            # 如果结束时间是次日，认为是通宵营业
            if '次日' in open_time_str or '翌日' in open_time_str:
                return True

            # 将时间转换为分钟数（从00:00开始）
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            target_minutes = 22 * 60  # 22:00

            # 判断是否跨天
            if end_minutes < start_minutes:
                # 跨天情况：从start到24:00，然后从00:00到end
                # 22:00在营业时间内的情况：
                # 1. start <= 22:00 <= 24:00
                # 2. 或者 00:00 <= 22:00 <= end（但22:00 > end很少见）
                if start_minutes <= target_minutes:
                    return True
            else:
                # 不跨天情况：start到end包含22:00
                if start_minutes <= target_minutes <= end_minutes:
                    return True

        except ValueError:
            continue

    return False


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")  


if __name__ == "__main__":
    main()

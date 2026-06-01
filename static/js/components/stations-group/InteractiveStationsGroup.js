import { BaseStationsGroup } from "./BaseStationsGroup.js"
import stateManager from "../../state/mapStateManager.js"
import { InteractiveStation } from "../station/InteractiveStation.js"
import { stations } from "../station/stations-list.js"

export class InteractiveStationsGroup extends BaseStationsGroup {
    constructor(map) {
        super(map)
        this.stations = Object.values(stations).map(stationData => new InteractiveStation(this.map, stationData));

        stateManager.subscribe((data) => {
            if (data.selectedRoute) {
                this.showOnlyRouteStations(data.selectedRoute.routeData);
            } else {
                this.show();
            }
        });
    }
}

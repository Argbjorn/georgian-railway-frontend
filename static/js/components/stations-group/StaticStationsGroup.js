import { BaseStationsGroup } from "./BaseStationsGroup.js"
import { StaticStation } from "../station/StaticStation.js"
import { stations } from "../station/stations-list.js"

export class StaticStationsGroup extends BaseStationsGroup {
    constructor(map) {
        super(map)
        this.stations = Object.values(stations).map(stationData => new StaticStation(this.map, stationData));
        this.hide() // hide all stations by default because stations show automatically after creation
    }
}

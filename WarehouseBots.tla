----------------------------- MODULE WarehouseBots -----------------------------
EXTENDS Naturals, TLC, Sequences

CONSTANT Bots, Zones

ASSUME Bots = {"Bot1", "Bot2", "Bot3"}
ASSUME Zones = {"Zone1", "Zone2", "Zone3", "Neutral"}

VARIABLES loc, moving

(*--algorithm lidar_bots
variables
    loc = [b \in Bots |-> "None"], \* current location of each bot
    moving = [b \in Bots |-> FALSE]; \* whether bot is moving

define
    NeutralSafe ==
        Cardinality({b \in Bots : loc[b] = "Neutral"}) <= 1

    ZoneExclusive ==
        \A b1, b2 \in Bots :
            b1 /= b2 => loc[b1] /= loc[b2] \/ loc[b1] = "None" \/ loc[b2] = "None"
end define;

process (Bot \in Bots)
variable targetZone, returnZone;
begin
  Loop:
    while (TRUE) {

        \* --- Choose a zone to cross (not Neutral, not current) ---
        targetZone := CHOOSE z \in Zones : z /= "Neutral" /\ z /= loc[Bot];

        \* --- Check LIDAR: is any other bot moving in that zone? ---
        if ~(\E other \in Bots : other /= Bot /\ loc[other] = targetZone /\ moving[other]) {
            moving[Bot] := TRUE;
            loc[Bot] := targetZone;
            moving[Bot] := FALSE;

            \* --- Enter Neutral Zone (assume it's mutually exclusive) ---
            loc[Bot] := "Neutral";

            \* --- Choose a zone to return to (not Neutral) ---
            returnZone := CHOOSE z \in Zones : z /= "Neutral";

            \* Check LIDAR again before re-entering ---
            if ~(\E other \in Bots : other /= Bot /\ loc[other] = returnZone /\ moving[other]) {
                moving[Bot] := TRUE;
                loc[Bot] := returnZone;
                moving[Bot] := FALSE;
            };

            \* --- Go idle ---
            loc[Bot] := "None";
        };
    }
end process;

end algorithm *)
===============================================================================

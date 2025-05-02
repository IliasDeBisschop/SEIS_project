----------------------------- MODULE tasks -----------------------------

EXTENDS Naturals, Sequences, TLC

VARIABLES tasks, bot_tasks

(* -- Constants -- *)
BOT_IDS == {"bot1", "bot2", "bot3"}  \* Set of bot IDs
TASK_ROWS == 0..19                   \* Rows for tasks
TASK_COLUMNS == 0..5                 \* Columns for tasks
MAX_TASKS == 20                      \* Maximum number of tasks allowed in the queue
None == << >>                        \* Placeholder for no task assigned

(* -- Initial State -- *)
Init ==
    /\ tasks = << >>  \* Initially, no tasks in the queue
    /\ bot_tasks = [bot \in BOT_IDS |-> None]  \* No tasks assigned to bots initially

(* -- Helper Functions -- *)
IsValidBot(bot) ==
    bot \in BOT_IDS

IsTaskAssignable(bot, task) ==
    \A other_bot \in BOT_IDS :
        IF other_bot = bot THEN TRUE
        ELSE 
            LET assigned_task == bot_tasks[other_bot]
            IN IF assigned_task = None THEN TRUE
               ELSE assigned_task[1] % 10 /= task[1] % 10

(* -- Transitions -- *)
GenerateTask(row, column) ==
    /\ row \in TASK_ROWS
    /\ column \in TASK_COLUMNS
    /\ Len(tasks) < MAX_TASKS
    /\ tasks' = Append(tasks, <<row, column>>)
    /\ UNCHANGED <<bot_tasks>>

AssignTask(bot) ==
    /\ IsValidBot(bot)
    /\ bot_tasks[bot] = None  \* Controleer of de bot geen taak heeft
    /\ tasks /= << >>         \* Controleer of er taken beschikbaar zijn
    /\ LET task == Head(tasks) IN
        /\ bot_tasks' = [bot_tasks EXCEPT ![bot] = task]  \* Wijs de eerste taak toe
        /\ tasks' = Tail(tasks)                          \* Verwijder de toegewezen taak uit de queue

CompleteTask(bot) ==
    /\ IsValidBot(bot)
    /\ bot_tasks[bot] /= None  \* Ensure the bot has a task assigned
    /\ bot_tasks' = [bot_tasks EXCEPT ![bot] = None]
    /\ UNCHANGED <<tasks>>

RemoveTaskOnce(seq, task) ==
    LET firstIdx == 
        CHOOSE i \in 1..Len(seq) : seq[i] = task
    IN
        SubSeq(seq, 1, firstIdx - 1) \o SubSeq(seq, firstIdx + 1, Len(seq))


(* -- State Transitions -- *)
Next ==
    \/ \E row \in TASK_ROWS, column \in TASK_COLUMNS : GenerateTask(row, column)
    \/ \E bot \in BOT_IDS : AssignTask(bot)
    \/ \E bot \in BOT_IDS : CompleteTask(bot)

(* -- Specification -- *)
Spec ==
    Init /\ [][Next]_<<tasks, bot_tasks>>

(* -- Invariants -- *)
Inv_TasksNotExceedMax ==
    Len(tasks) <= MAX_TASKS

Inv_BotTasksValid ==
    \A bot \in BOT_IDS : 
        bot_tasks[bot] = None \/
        (\E row \in TASK_ROWS, col \in TASK_COLUMNS : bot_tasks[bot] = <<row, col>>)

THEOREM Spec =>
    Inv_TasksNotExceedMax /\ Inv_BotTasksValid



===============================================================================
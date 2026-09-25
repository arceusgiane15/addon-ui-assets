// Runs a command for one player from the dimension (server source) instead of from the player.
// Commands sent *as* a player can be refused with "Cheats aren't enabled in this world".
export function runAs(player, command) {
  try {
    const tag = `sid_${player.id}`;
    if (!player.hasTag(tag)) player.addTag(tag);
    return player.dimension.runCommandAsync(command.replace(/@s(?![\w[])/g, `@a[tag="${tag}"]`)).catch(() => {});
  } catch (e) {
    return Promise.resolve();
  }
}

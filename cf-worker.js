addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const { pathname } = new URL(request.url);

  if (isReleaseRequest(pathname)) {
    const repo = getRepoFromPath(pathname);

    try {
      const latestRelease = await fetchLatestRelease(repo);

      if (!latestRelease) {
        throw new Error('Failed to fetch latest release');
      }

      const timeUntilNextRelease = calculateTimeUntilNextRelease(
        latestRelease.published_at
      );

      const { message, color } = getMessageAndColor(timeUntilNextRelease);

      const output = {
        schemaVersion: 1,
        style: 'for-the-badge',
        label: 'Next Release',
        message,
        color
        //timeUntilNextRelease,
        //timeUntilNextReleaseInDays: Math.floor(timeUntilNextRelease - (24 * 60 * 60 * 1000))
      };

      return new Response(JSON.stringify(output), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
  } else {
    return new Response('Did you mean /shield/gh/subwaybooster?');
  }
}

function isReleaseRequest(path) {
  const pathSegments = path.split('/');
  return (
    pathSegments.length === 4 &&
    pathSegments[1] === 'shield' &&
    pathSegments[2] === 'gh'
  );
}

function getRepoFromPath(path) {
  const pathSegments = path.split('/');
  return pathSegments[3];
}

function calculateTimeUntilNextRelease(releaseDate) {
  const MILLISECONDS_PER_RELEASE_CYCLE = (21 * 24 + 8) * 60 * 60 * 1000;

  const timeSinceRelease = Date.now() - new Date(releaseDate);
  return (
    MILLISECONDS_PER_RELEASE_CYCLE -
    (timeSinceRelease % MILLISECONDS_PER_RELEASE_CYCLE)
  );
}

function getMessageAndColor(timeUntilNextRelease) {
  const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;

  const data = [
    { message: 'Today', color: '3de24e', days: 0 }, // green
    { message: 'Tomorrow', color: 'ffff00', days: 1 }, // yellow
    { message: 'This week', color: '0000ff', days: 6 }, // blue
    { message: 'Next week', color: '00ffff', days: 8 }, // cyan
    { message: 'Really Soon', color: 'ffa500', days: 12 }, // orange
    { message: 'In the Future', color: '800080', days: 15 }, // purple
    { message: 'In a While', color: 'ffc0cb', days: 18 }, // pink
    { message: 'Not for a While', color: 'ff0000', days: 21 } // red
  ];

  const daysUntilNextRelease = Math.floor(
    timeUntilNextRelease / MILLISECONDS_PER_DAY
  );

  let closestInterval = data[0];

  for (const item of data) {
    if (daysUntilNextRelease <= item.days) {
      closestInterval = item;
      break;
    }
  }

  return { message: closestInterval.message, color: closestInterval.color };
}

async function fetchLatestRelease(repo) {
  const owner = 'HerrErde';
  const token = 'ghp_';
  const projectname = 'SubwaySurfersApi';

  const headers = {
    'User-Agent': projectname,
    Authorization: `token ${token}`
  };

  const response = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/releases/latest`,
    { headers }
  );

  if (!response.ok) {
    return null;
  }

  return response.json();
}

addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const { pathname } = new URL(request.url);

  if (isReleaseRequest(pathname)) {
    const repo = getRepoFromPath(pathname);

    try {
      const latestRelease = await fetchMajorRelease(repo);

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
      };

      return new Response(JSON.stringify(output), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*' // CORS
        }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*' // CORS
        }
      });
    }
  } else if (pathname.startsWith('/gh/') && pathname.split('/').length === 3) {
    const repo = getRepoFromPath(pathname);

    try {
      const latestRelease = await fetchMajorRelease(repo);

      if (!latestRelease) {
        throw new Error('Failed to fetch latest release');
      }

      const timeUntilNextRelease = calculateTimeUntilNextRelease(
        latestRelease.published_at
      );

      const daysUntilNextRelease = Math.ceil(
        timeUntilNextRelease / (1000 * 60 * 60 * 24)
      );
      const nextReleaseDate = new Date(Date.now() + timeUntilNextRelease);
      const formattedReleaseDate = nextReleaseDate.toLocaleString();

      const output = {
        days_count: `${daysUntilNextRelease} ${
          daysUntilNextRelease > 1 ? 'days' : 'day'
        }`,
        releaseDate: formattedReleaseDate
      };

      return new Response(JSON.stringify(output), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*' // CORS
        }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*' // CORS
        }
      });
    }
  } else {
    return new Response('Did you mean /gh/{repo}/shield?', {
      headers: { 'Access-Control-Allow-Origin': '*' } // CORS
    });
  }
}

function isReleaseRequest(path) {
  const pathSegments = path.split('/');
  return (
    pathSegments.length === 4 &&
    pathSegments[1] === 'gh' &&
    pathSegments[3] === 'shield'
  );
}

function getRepoFromPath(path) {
  const pathSegments = path.split('/');
  return pathSegments[2];
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
    { message: 'Day after Tomorrow', color: 'ffa500', days: 2 }, // orange
    { message: 'Just Around the Corner', color: 'f9bdbd', days: 3 }, // pink
    { message: 'In Sight', color: '4682b4', days: 4 }, // steelblue
    { message: 'Just Ahead', color: '9932cc', days: 5 }, // darkorchid
    { message: 'Not Far Away', color: '32cd32', days: 7 }, // limegreen
    { message: 'Next week', color: '00ffff', days: 8 }, // cyan
    { message: 'After Next week', color: '2138AB', days: 10 }, // blue
    { message: 'Drawing Near', color: 'ff4500', days: 11 }, // orangered
    { message: 'Really Soon', color: 'FF7F00', days: 12 }, // orange
    { message: 'In a While', color: 'ffc0cb', days: 15 }, // pink
    { message: 'Approaching', color: '8b008b', days: 16 }, // darkmagenta
    { message: 'Not for a While', color: '800080', days: 17 }, // purple
    { message: 'In the Near Future', color: '20b2aa', days: 19 }, // lightseagreen
    { message: 'In the Future', color: 'ff0000', days: 21 } // red
  ];

  const daysUntilNextRelease = timeUntilNextRelease / MILLISECONDS_PER_DAY;

  let closestInterval = data[0];

  for (const item of data) {
    if (daysUntilNextRelease <= item.days) {
      closestInterval = item;
      break;
    }
  }

  return { message: closestInterval.message, color: closestInterval.color };
}

async function fetchMajorRelease(repo) {
  const owner = 'HerrErde';
  const token = 'ghp_';
  const projectname = 'SubwaySurfersApi';

  const headers = {
    'User-Agent': projectname
  };
  if (token) {
    headers.Authorization = `token ${token}`;
  }

  const response = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/releases`,
    { headers }
  );

  if (!response.ok) {
    return null;
  }

  const releases = await response.json();

  // Find the first release with a tag like x.x.0
  for (const release of releases) {
    const tag = release.tag_name;
    if (/^v?\d+\.\d+\.0$/.test(tag)) {
      return release;
    }
  }

  return null;
}

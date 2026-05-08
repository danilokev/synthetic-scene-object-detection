%% ============================================================
%%  ARCHIVO: escena3mat.m
%%  Escena 3 – Vista cenital ortográfica, FONDO TRANSPARENTE
%%  Detección de siluetas: canal alfa (RGBA PNG) o umbral Otsu
%% ============================================================
clear; clc; close all;

dir_datos  = fullfile('datos',   'escena3');
dir_salida = fullfile('salidas', 'escena3');
if ~exist(dir_salida,'dir'), mkdir(dir_salida); end

secs = {'escena3_1','escena3_2','escena3_3'};

for e = 1:numel(secs)
    nom  = secs{e};
    din  = fullfile(dir_datos,  nom);
    dout = fullfile(dir_salida, [nom '_salida']);
    if ~exist(dout,'dir'), mkdir(dout); end

    arch = dir(fullfile(din,'*.png'));
    if isempty(arch), fprintf('Sin imágenes en %s\n', din); continue; end

    vid = VideoWriter(fullfile(dir_salida, [nom '_salida.mp4']), 'MPEG-4');
    vid.FrameRate = 1; open(vid);

    for k = 1:numel(arch)
        fpath = fullfile(din, arch(k).name);

        % Leer PNG con posible canal alfa (CYCLES renderiza RGBA)
        [img, ~, alpha] = imread(fpath);

        if ~isempty(alpha) && numel(unique(alpha)) > 1
            % --- Canal alfa disponible: silueta perfecta ---
            bw = alpha > 128;
        else
            % --- Fallback: umbralización de la imagen gris ---
            gris = rgb2gray(img);
            T = graythresh(gris);
            bw = imbinarize(gris, T);
            % Si más de la mitad está marcado, invertir
            % (depende de si el fondo es negro o blanco)
            if sum(bw(:)) > numel(bw)*0.6, bw = ~bw; end
        end

        bw = imopen(bw,  strel('disk', 3));
        bw = imclose(bw, strel('disk', 6));
        bw = imfill(bw,  'holes');
        bw = bwareaopen(bw, 300);

        % Compositar sobre fondo blanco para que el vídeo se vea bien
        if ~isempty(alpha)
            a3 = repmat(double(alpha)/255, [1 1 3]);
            fondo = ones(size(img),'like',img) * 255;
            img = uint8(double(img).*a3 + double(fondo).*(1-a3));
        end

        st = regionprops(bw, 'Centroid','BoundingBox','Area','Perimeter');
        io = img; nd = 0;

        for i = 1:numel(st)
            A = st(i).Area; if A < 300, continue; end
            nd = nd + 1;
            cx = st(i).Centroid(1);  cy = st(i).Centroid(2);
            bb = st(i).BoundingBox;  P  = max(st(i).Perimeter, 1);

            circ = 4*pi*A / P^2;
            asp  = bb(3) / max(bb(4), 1);

            if     circ > 0.72,           et = 'Cilindro'; c = 'green';
            elseif asp  > 1.4 || asp < 0.70, et = 'Prisma';   c = 'blue';
            else,                          et = 'Cubo';     c = 'red';
            end

            io = insertShape(io,  'Rectangle', bb, 'Color',c, 'LineWidth',2);
            io = insertMarker(io, [cx cy],      '+', 'Color',c, 'Size',15);
            io = insertText(io,   [cx-30 cy-22], et, 'FontSize',11, ...
                'TextColor',c, 'BoxColor','white', 'BoxOpacity',0.65);
        end

        io = insertText(io, [5 5], sprintf('F%d/%d | Siluetas:%d', k, numel(arch), nd), ...
            'FontSize',12,'TextColor','black','BoxColor','white','BoxOpacity',0.8);
        imwrite(io, fullfile(dout, arch(k).name));
        writeVideo(vid, io);
    end
    close(vid);
    fprintf('✓ %s_salida generada\n', nom);
end
fprintf('=== Escena 3 completa ===\n');